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
    get_custom_release_branch,

    # Test
    get_test_branch_input
)

from ui.display import (
    show_error_msg,
    show_input_error_msg
)

from pipeline.git_operations import (
    get_release_branches,
    get_latest_release_branch,
    validate_release_branch,

    # Test
    get_Test_branches,
    validate_test_branch
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
        show_error_msg("No release branches found.")
        return None

    branch_choice = get_release_branch_input()
    if branch_choice == "l":
        return get_latest_release_branch(release_branch_list)
    elif branch_choice == "c":
        custom_release_branch = get_custom_release_branch()
        validated_branch = validate_release_branch(custom_release_branch, release_branch_list)
        if validated_branch is None:
            show_input_error_msg("Release branch does not exist.")
            return get_required_release_branch(repo_path)
        return validated_branch

    return None


# Test
def get_test_branch(repo_path: str) -> str | None:
    """
    ONLY FOR TEST <dev_mode>
    Returns the test branch required for the build.
    The user selects one of the available origin/test/* branches.
    """
    test_branch_list = get_Test_branches(repo_path)
    if not test_branch_list:
        show_error_msg("No test branches found.")
        return None

    test_branch = get_test_branch_input(test_branch_list)
    validated_branch = validate_test_branch(test_branch, test_branch_list)
    if validated_branch is None:
        show_input_error_msg("Test branch does not exist.")
        return get_test_branch(repo_path)

    return validated_branch

