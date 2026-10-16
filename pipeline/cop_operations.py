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

from pipeline.command_runner import run_command_live

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
