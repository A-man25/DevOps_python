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
# Every command runs through run_command_live, which shows
# one live progress line instead of COP's raw output.
#
# ============================================================

import os

from pipeline.command_runner import run_command_live

# cop login exits with code 0 even when the login fails,
# so this text is the only sign that it worked
COP_LOGIN_SUCCESS_TEXT = "Successfully logged in to MyConfigura"

def is_cop_login_set() -> bool:
    """Checks if the MyConfigura login is already set for COP."""
    return bool(os.environ.get("CETDEV_MC_USERNAME")) and bool(os.environ.get("CETDEV_MC_PASSWORD"))

def set_cop_login(email: str, password: str):
    """
    Gives COP the MyConfigura login through environment variables.
    COP reads them whenever it needs to log in (cop upload does),
    so it never has to ask.
    Only set for this run, nothing is saved to disk.
    """
    os.environ["CETDEV_MC_USERNAME"] = email
    os.environ["CETDEV_MC_PASSWORD"] = password

def clear_cop_login():
    """Forgets the MyConfigura login for this run, e.g. after a wrong password."""
    os.environ.pop("CETDEV_MC_USERNAME", None)
    os.environ.pop("CETDEV_MC_PASSWORD", None)

def cop_login(repo_path: str) -> bool:
    """
    Logs in to MyConfigura with the login set by set_cop_login,
    so a wrong email or password is found before the build starts.

    COP's exit code is 0 even when the login fails, so the login
    only counts as done when COP prints COP_LOGIN_SUCCESS_TEXT.
    """
    cop_command = ["cop", "login"]
    email = os.environ.get("CETDEV_MC_USERNAME", "")
    return run_command_live(cop_command, repo_path, "COP LOGIN", email, COP_LOGIN_SUCCESS_TEXT)

def cop_clean(repo_path: str) -> bool:
    """Runs 'cop clean' in the specified build workspace."""
    cop_command = ["cop", "clean"]
    return run_command_live(cop_command, repo_path, "COP CLEAN")


def cop_repair(repo_path: str) -> bool:
    """Runs 'cop repair' in the specified build workspace."""
    cop_command = ["cop", "repair"]
    return run_command_live(cop_command, repo_path, "COP REPAIR")


def cop_set_versions(extension_groups: list[str], build_version: str, repo_path: str) -> bool:
    """
    Sets the version for the selected extension groups.

    Example:
    cop setversions [hon] [asi]
    /version=16.5.9.11 /notag /nocommit
    """
    cop_command = ["cop", "setversions", *extension_groups, f"/version={build_version}", "/notag", "/nocommit"]
    return run_command_live(cop_command, repo_path, "COP SETVERSIONS", build_version)


def cop_make(extension_groups: list[str], repo_path: str) -> bool:
    """Builds the selected HNI extension groups."""
    cop_command = ["cop", "make", *extension_groups]
    return run_command_live(cop_command, repo_path, "COP MAKE")


def cop_upload(extension_groups: list[str], upload_name: str, repo_path: str) -> bool:
    """Uploads the selected HNI extension builds."""
    cop_command = ["cop", "upload", *extension_groups, f"/uploadname={upload_name}"]
    return run_command_live(cop_command, repo_path, "COP UPLOAD", upload_name)
