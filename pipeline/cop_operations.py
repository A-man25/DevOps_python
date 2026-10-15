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
    print("/n----------Executing COP-CLEAN-------------")
    cop_command = ["cop", "clean"]
    print(" ".join(cop_command))
    result = subprocess.run(cop_command, cwd=repo_path, text=True)
    if result.returncode != 0:
        print("COP clean failed.")
        print(result.stderr)
        return False

    print("COP clean completed successfully.")
    return True


def cop_repair(repo_path: str) -> bool:
    """Runs 'cop repair' in the specified build workspace."""
    print("/n-------------Executing COP-REPAIR------------")
    cop_command = ["cop", "repair"]
    print(" ".join(cop_command))
    result = subprocess.run(cop_command, cwd=repo_path, text=True)
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

    print("/n-------Executing COP SET-VERSION-----------------")
    cop_command = ["cop", "setversions", *extension_groups, f"/version={build_version}", "/notag", "/nocommit"]
    print(" ".join(cop_command))
    result = subprocess.run(cop_command, cwd=repo_path, text=True)

    if result.returncode != 0:
        print("COP setversions failed.")
        print(result.stderr)
        return False

    print(
        f"COP setversions completed successfully "
        f"for version {build_version}."
    )

    return True


import subprocess


def cop_make(extension_groups: list[str], repo_path: str) -> bool:

    cop_command = ["cop", "make", *extension_groups]

    print("\nExecuting:")
    print(" ".join(cop_command))
    print()

    process = subprocess.Popen(cop_command, cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    progress_active = False

    for line in process.stdout:
        line = line.strip()
        if "Work in progress" in line:
            print(f"\r{line:<100}", end="", flush=True)
            progress_active = True
        else:
            if progress_active:
                print()
                progress_active = False
            print(line)
    process.wait()

    if process.returncode != 0:
        print("\nCOP build failed.")
        return False

    print("\nCOP build completed successfully.")
    return True

def cop_upload(extension_groups: list[str], upload_name: str, repo_path: str) -> bool:
    """Uploads the selected HNI extension builds."""
    print("/n-----------Executing COP-UPLOAD---------------")
    cop_command = ["cop", "upload", *extension_groups, f"/uploadname={upload_name}"]
    print(" ".join(cop_command))
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