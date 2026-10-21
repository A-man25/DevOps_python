# ============================================================
# Project      : HNI Build Automation
# File         : preflight.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Checks this PC before anything is asked or built, so problems
# are found in seconds, not halfway through a 20-minute build.
#
# Checks:
# - Git and COP are installed
# - The workspace folder exists and is a Git repo with 'origin'
# - Git knows who you are (needed for the build commit)
# - No merge/rebase is half-finished
# - No uncommitted changes to tracked files (they would end up
#   mixed into the build, or block the branch checkout)
#
# ============================================================

import os
import shutil

from pipeline.git_operations import (
    is_git_repo,
    has_origin_remote,
    has_git_identity,
    get_operation_in_progress,
    get_uncommitted_tracked_files
)

from ui.display import (
    show_preflight_header,
    show_check,
    show_check_details
)

MAX_FILES_SHOWN = 10

def run_preflight_checks(repo_path: str) -> bool:
    """Runs every check in order and stops at the first one that fails. Returns True if all passed."""
    show_preflight_header()

    git_path = shutil.which("git")
    if not git_path:
        show_check("Git installed", False, "git was not found. Install Git for Windows.")
        return False
    show_check("Git installed", True, git_path)

    cop_path = shutil.which("cop")
    if not cop_path:
        show_check("COP installed", False, "cop was not found. Install CET Developer.")
        return False
    show_check("COP installed", True, cop_path)

    if not os.path.isdir(repo_path):
        show_check("Workspace folder", False, f"{repo_path} does not exist.")
        show_check_details(["Set the right folder for this PC with:",
                            'setx HNI_BUILD_REPO_PATH "C:\\CetDev\\<workspace>\\extensions\\custom"',
                            "then open a new window and start the tool again."])
        return False

    if not is_git_repo(repo_path):
        show_check("Workspace folder", False, f"{repo_path} is not a Git repo.")
        return False
    show_check("Workspace folder", True, repo_path)

    if not has_origin_remote(repo_path):
        show_check("Server (origin)", False, "the repo has no 'origin' remote.")
        return False
    show_check("Server (origin)", True)

    if not has_git_identity(repo_path):
        show_check("Git name and email", False, "Git does not know who you are (needed for the commit).")
        show_check_details(['git config --global user.name "Your Name"',
                            'git config --global user.email "you@hni-asia.com"'])
        return False
    show_check("Git name and email", True)

    operation = get_operation_in_progress(repo_path)
    if operation:
        show_check("No unfinished Git work", False, f"a {operation} is not finished in this repo.")
        show_check_details([f"Finish it, or cancel it with: git {operation} --abort"])
        return False
    show_check("No unfinished Git work", True)

    uncommitted_files = get_uncommitted_tracked_files(repo_path)
    if uncommitted_files:
        show_check("No uncommitted changes", False, f"{len(uncommitted_files)} file(s) are changed but not committed:")
        show_check_details(uncommitted_files[:MAX_FILES_SHOWN])
        if len(uncommitted_files) > MAX_FILES_SHOWN:
            show_check_details([f"... and {len(uncommitted_files) - MAX_FILES_SHOWN} more"])
        show_check_details(["Commit them, or put them aside with: git stash",
                            "(so they are not mixed into the build commit)"])
        return False
    show_check("No uncommitted changes", True)

    return True
