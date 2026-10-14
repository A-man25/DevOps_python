# ============================================================
# Project      : HNI Build Automation
# File         : cop_operations.py
# Author       : Aman Rajesh Choudhari
# Created      : 14-Oct-2026
#
# Description:
# Handles COP command execution required by the HNI build
# automation pipeline.
#
# Responsibilities:
# - Clean the build workspace using COP
# - Repair the build workspace using COP
# - Set extension versions
# - Build selected HNI extensions
# - Upload successful builds
# - Report COP command success or failure
#
# ============================================================

import subprocess


def cop_clean(repo_path: str) -> bool:
    """Runs 'cop clean' in the specified build workspace."""
    cop_command = ["cop", "clean"]
    result = subprocess.run(cop_command, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print("COP clean failed.")
        print(result.stderr)
        return False

    print("COP clean completed successfully.")
    return True


def cop_repair(repo_path: str) -> bool:
    """Runs 'cop repair' in the specified build workspace."""
    cop_command = ["cop", "repair"]
    result = subprocess.run(cop_command, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print("COP repair failed.")
        print(result.stderr)
        return False

    print("COP repair completed successfully.")
    return True


def cop_set_versions(extension_groups: list[str], build_version: str, repo_path: str) -> bool:
    """
    Sets the version for the selected extension groups.

    Example:
    cop setversions [hon] [asi]
    /version=16.5.9.11 /notag /nocommit
    """
    cop_command = ["cop", "setversions", *extension_groups, f"/version={build_version}", "/notag", "/nocommit"]
    result = subprocess.run(cop_command, cwd=repo_path, capture_output=True, text=True)

    if result.returncode != 0:
        print("COP setversions failed.")
        print(result.stderr)
        return False

    print(
        f"COP setversions completed successfully "
        f"for version {build_version}."
    )

    return True


def cop_make(extension_groups: list[str], repo_path: str) -> bool:
    """Builds the selected HNI extension groups."""
    cop_command = ["cop", "make", *extension_groups]

    result = subprocess.run(cop_command, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print("COP build failed.")
        print(result.stderr)
        return False

    print("COP build completed successfully.")
    return True


def cop_upload(extension_groups: list[str], upload_name: str, repo_path: str) -> bool:
    """Uploads the selected HNI extension builds."""
    cop_command = ["cop", "upload", *extension_groups, f"/uploadname={upload_name}"]

    result = subprocess.run(cop_command, cwd=repo_path, capture_output=True, text=True)

    if result.returncode != 0:
        print("COP upload failed.")
        print(result.stderr)
        return False

    print(
        f"COP upload completed successfully: "
        f"{upload_name}"
    )

    return True