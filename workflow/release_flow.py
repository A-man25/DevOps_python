# ============================================================
# Project      : HNI Build Automation
# File         : release_flow.py
# Author       : Aman Rajesh Choudhari
# Created      : 14-Oct-2026
#
# Description:
# Handles the workflow for determining the required HNI
# release branch.
#
# Responsibilities:
# - Fetch available release branches
# - Ask whether latest or custom branch is required
# - Determine the latest release branch
# - Validate custom release branch input
# ============================================================

from ui.input_handler import (
    get_release_branch_input,
    get_custom_release_branch
)

from pipeline.git_operations import (
    get_release_branches,
    get_latest_release_branch,
    validate_release_branch
)


def get_required_release_branch(repo_path: str) -> str | None:
    """
    Returns the release branch required for the build.
    The user may select either:
    - Latest available release branch
    - Custom release branch
    """
    release_branch_list = get_release_branches(repo_path)
    if not release_branch_list:
        print("No release branches found.")
        return None

    branch_choice = get_release_branch_input()
    if branch_choice == "l":
        return get_latest_release_branch(release_branch_list)
    elif branch_choice == "c":
        custom_release_branch = get_custom_release_branch()
        validated_branch = validate_release_branch(custom_release_branch, release_branch_list)
        if validated_branch is None:
            print("Release branch does not exist.")
            return get_required_release_branch(repo_path)
        return validated_branch

    return None