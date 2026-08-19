import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

CURRENT_FOLDER = Path(__file__).resolve().parent
ROOT = CURRENT_FOLDER.parent

WORKING_SERVER = ROOT / "working_server"
RELEASE_DIR = ROOT / "release"

CONSISTENT_FILES_LIST = CURRENT_FOLDER / "consistent_afterbuild_files.txt"
CONSISTENT_BACKUP = ROOT / ".consistent_backup"

SERVER_ARCHIVE = RELEASE_DIR / "SS14.Server_win-x64.zip"

BUILDING = True
BUILD_PACKAGER = True

PACKAGE_CLIENT = False

CONFIGURATION = "Release"
PLATFORM = "win-x64"


def run(command):
    """Run a command and stop if it fails."""
    print(f"\n>>> {' '.join(command)}\n")

    result = subprocess.run(command, cwd=ROOT)

    if result.returncode != 0:
        print(f"\nFAILED ({result.returncode})")
        sys.exit(result.returncode)


def read_consistent_files():
    """
    Read paths from consistent_afterbuild_files.txt.

    Paths are relative to working_server/.
    Empty lines and lines starting with '#' are ignored.
    """
    if not CONSISTENT_FILES_LIST.exists():
        print(
            f"WARNING: {CONSISTENT_FILES_LIST.name} "
            f"does not exist."
        )
        return []

    paths = []

    with CONSISTENT_FILES_LIST.open(
        "r",
        encoding="utf-8"
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            paths.append(Path(line))

    return paths


def backup_consistent_files():
    """
    Save files/folders from working_server that are listed in
    consistent_afterbuild_files.txt.
    """
    print("\n=== Backing up consistent files ===")

    paths = read_consistent_files()

    if not paths:
        print("Nothing to backup.")
        return

    # Remove old backup.
    shutil.rmtree(
        CONSISTENT_BACKUP,
        ignore_errors=True
    )

    CONSISTENT_BACKUP.mkdir(
        parents=True,
        exist_ok=True
    )

    for relative_path in paths:
        source = WORKING_SERVER / relative_path
        backup = CONSISTENT_BACKUP / relative_path

        if not source.exists():
            print(
                f"WARNING: Not found in working_server: "
                f"{relative_path}"
            )
            continue

        print(f"Backing up: {relative_path}")

        backup.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if source.is_dir():
            shutil.copytree(
                source,
                backup
            )
        else:
            shutil.copy2(
                source,
                backup
            )

    print("Backup complete.")


def build_projects():
    """
    Build server and client.
    """
    print("\n=== Building server and client ===")

    run([
        "dotnet",
        "build",
        "-c",
        CONFIGURATION
    ])


def build_packager():
    """
    Build Content.Packaging.
    """
    print("\n=== Building packager ===")

    run([
        "dotnet",
        "build",
        "Content.Packaging",
        "-c",
        CONFIGURATION
    ])


def package_server():
    """
    Package server.
    """
    print("\n=== Packaging server ===")

    run([
        "dotnet",
        "run",
        "--project",
        "Content.Packaging",
        "server",
        "--hybrid-acz",
        "--platform",
        PLATFORM
    ])


def package_client():
    """
    Package client.
    """
    print("\n=== Packaging client ===")

    run([
        "dotnet",
        "run",
        "--project",
        "Content.Packaging",
        "client",
        "--platform",
        PLATFORM
    ])


def clear_working_server():
    """
    Completely clear working_server/.
    """
    print("\n=== Clearing working_server ===")

    if WORKING_SERVER.exists():
        shutil.rmtree(WORKING_SERVER)

    WORKING_SERVER.mkdir(
        parents=True,
        exist_ok=True
    )


def extract_server():
    """
    Extract release/SS14.Server_win-x64.zip
    into working_server/.
    """
    print("\n=== Extracting server ===")

    if not SERVER_ARCHIVE.exists():
        print(
            f"ERROR: Server archive not found:\n"
            f"{SERVER_ARCHIVE}"
        )
        sys.exit(1)

    print(f"Archive: {SERVER_ARCHIVE}")
    print(f"Destination: {WORKING_SERVER}")

    with zipfile.ZipFile(
        SERVER_ARCHIVE,
        "r"
    ) as archive:
        archive.extractall(WORKING_SERVER)


def restore_consistent_files():
    """
    Restore files/folders from the backup into working_server/.
    """
    print("\n=== Restoring consistent files ===")

    paths = read_consistent_files()

    if not paths:
        print("Nothing to restore.")
        return

    if not CONSISTENT_BACKUP.exists():
        print(
            "ERROR: Consistent backup does not exist."
        )
        sys.exit(1)

    for relative_path in paths:
        backup = CONSISTENT_BACKUP / relative_path
        target = WORKING_SERVER / relative_path

        if not backup.exists():
            print(
                f"WARNING: Backup not found: "
                f"{relative_path}"
            )
            continue

        print(f"Restoring: {relative_path}")

        # Remove the newly-built version.
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

        target.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if backup.is_dir():
            shutil.copytree(
                backup,
                target
            )
        else:
            shutil.copy2(
                backup,
                target
            )

    print("Restore complete.")


def cleanup_backup():
    """
    Remove temporary backup after successful restore.
    """
    print("\n=== Cleaning backup ===")

    shutil.rmtree(
        CONSISTENT_BACKUP,
        ignore_errors=True
    )


def clean():
    """
    Clean build artifacts and release files.
    """
    print("\n=== Cleaning build artifacts ===")

    for folder in ROOT.rglob("bin"):
        shutil.rmtree(
            folder,
            ignore_errors=True
        )

    for folder in ROOT.rglob("obj"):
        shutil.rmtree(
            folder,
            ignore_errors=True
        )

    shutil.rmtree(
        RELEASE_DIR,
        ignore_errors=True
    )


def main():

    # ---------------------------------------------------------
    # 1. Backup files that must survive the build
    # ---------------------------------------------------------

    backup_consistent_files()

    # ---------------------------------------------------------
    # 2. Build server + client
    # ---------------------------------------------------------

    if BUILDING:
        build_projects()

    # ---------------------------------------------------------
    # 3. Build packager if requested
    # ---------------------------------------------------------

    if BUILD_PACKAGER:
        build_packager()

    # ---------------------------------------------------------
    # 4. Package server
    # ---------------------------------------------------------

    package_server()

    # ---------------------------------------------------------
    # 5. Package client
    # ---------------------------------------------------------

    if PACKAGE_CLIENT:
        package_client()

    # ---------------------------------------------------------
    # 6. Clear working_server
    # ---------------------------------------------------------

    clear_working_server()

    # -----------------------------------------------------
    # 7. Extract newly packaged server
    # -----------------------------------------------------

    extract_server()

    # -----------------------------------------------------
    # 8. Restore files that should remain consistent
    # -----------------------------------------------------

    restore_consistent_files()

    # -----------------------------------------------------
    # Cleanup backup
    # -----------------------------------------------------

    cleanup_backup()

    print("\nDone!")

    if RELEASE_DIR.exists():
        print(f"Release folder: {RELEASE_DIR}")

    if WORKING_SERVER.exists():
        print(f"Working server: {WORKING_SERVER}")


if __name__ == "__main__":
    main()