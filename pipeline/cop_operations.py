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
# - Show COP make output live and cleanly
# - Pass the MyConfigura login to COP
#
# ============================================================

import os
import subprocess
import time

from ui.display import (
    show_cop_make_header,
    show_cop_make_summary,
    show_cop_make_errors_msg
)

def is_cop_login_set() -> bool:
    """Checks if the MyConfigura login is already set for COP."""
    return bool(os.environ.get("CETDEV_MC_USERNAME")) and bool(os.environ.get("CETDEV_MC_PASSWORD"))

def set_cop_login(email: str, password: str):
    """
    Gives COP the MyConfigura login through environment variables,
    so COP commands don't keep asking for it.
    Only set for this run, nothing is saved to disk.
    """
    os.environ["CETDEV_MC_USERNAME"] = email
    os.environ["CETDEV_MC_PASSWORD"] = password

def cop_login(repo_path: str) -> bool:
    """Logs in to MyConfigura using the login set by set_cop_login."""
    print("\n-----------Executing COP-LOGIN----------------")
    cop_command = ["cop", "login"]
    print(" ".join(cop_command))
    result = subprocess.run(cop_command, cwd=repo_path, text=True)
    if result.returncode != 0:
        print("COP login failed. Check your MyConfigura email and password.")
        return False

    print("COP login completed successfully.")
    return True

def cop_clean(repo_path: str) -> bool:
    """Runs 'cop clean' in the specified build workspace."""
    print("\n----------Executing COP-CLEAN-------------")
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
    print("\n-------------Executing COP-REPAIR------------")
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

    print("\n-------Executing COP SET-VERSION-----------------")
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


def cop_make(extension_groups: list[str], repo_path: str) -> bool:
    """
    Builds the selected HNI extension groups.

    COP writes straight to the console, the same as running it
    from a .bat file, so its live status redraws cleanly in place.
    Do not capture this output (stdout=PIPE): COP needs the real
    console to redraw its status lines.
    """
    cop_command = ["cop", "make", *extension_groups]
    show_cop_make_header(cop_command)

    start_time = time.monotonic()
    result = subprocess.run(cop_command, cwd=repo_path)
    build_success = result.returncode == 0
    show_cop_make_summary(time.monotonic() - start_time, build_success)

    if not build_success:
        # Shows only the targets that failed, with a few errors each
        show_cop_make_errors_msg()
        subprocess.run(["cop", "make", *extension_groups, "/printLastErrorsCompact"], cwd=repo_path)
        print("COP build failed.")
        return False

    print("COP build completed successfully.")
    return True

def cop_upload(extension_groups: list[str], upload_name: str, repo_path: str) -> bool:
    """Uploads the selected HNI extension builds."""
    print("\n-----------Executing COP-UPLOAD---------------")
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