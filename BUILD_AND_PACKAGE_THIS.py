import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PACKAGE_CLIENT = False
CONFIGURATION = "Release"
PLATFORM = "win-x64"


def run(command):
    print(f"\n>>> {' '.join(command)}\n")
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        print(f"\nFAILED ({result.returncode})")
        sys.exit(result.returncode)


def clean():
    print("Cleaning...")

    for folder in ROOT.rglob("bin"):
        shutil.rmtree(folder, ignore_errors=True)

    for folder in ROOT.rglob("obj"):
        shutil.rmtree(folder, ignore_errors=True)

    shutil.rmtree(ROOT / "release", ignore_errors=True)


def main():
    # Optional
    # clean()

    run([
        "dotnet",
        "build",
        "-c",
        CONFIGURATION
    ])

    run([
        "dotnet",
        "build",
        "Content.Packaging",
        "-c",
        CONFIGURATION
    ])

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

    if PACKAGE_CLIENT:
        run([
            "dotnet",
            "run",
            "--project",
            "Content.Packaging",
            "client",
            "--platform",
            PLATFORM
        ])

    print("\nDone!")

    release = ROOT / "release"
    if release.exists():
        print(f"Release folder: {release}")


if __name__ == "__main__":
    main()