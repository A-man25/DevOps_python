# ============================================================
# Project      : HNI Build Automation
# File         : beta_build_flow.py
# Author       : Aman Rajesh Choudhari
# Created      : 14-Oct-2026
#
# Description:
# Coordinates the complete HNI Beta build workflow.
#
# Responsibilities:
# - Checkout the required release branch
# - Pull the latest source code
# - Clean and repair the build workspace
# - Set extension versions
# - Verify Git changes before committing
# - Commit and tag the build version
# - Build selected extensions
# - Upload the Beta build
#
# ============================================================

from pipeline.git_operations import (
    checkout_release_branch,
    pull_latest_changes,
    get_changed_files,
    stage_changes,
    commit_build_version,
    create_build_tag
)

from pipeline.cop_operations import (
    cop_clean,
    cop_repair,
    cop_set_versions,
    cop_make,
    cop_upload
)

from ui.input_handler import get_git_changes_confirmation

def run_beta_build(
    repo_path: str,
    release_branch: str,
    extension_groups: list[str],
    build_version: str,
    upload_name: str
) -> bool:
    """
    Executes the HNI Beta build pipeline.

    Returns True if the complete build succeeds.
    Returns False if any pipeline stage fails or is cancelled.
    """

    # --------------------------------------------------------
    # 1. Checkout release branch
    # --------------------------------------------------------

    if not checkout_release_branch(
        release_branch,
        repo_path
    ):
        print("Beta build stopped during branch checkout.")
        return False

    # --------------------------------------------------------
    # 2. Pull latest source
    # --------------------------------------------------------

    if not pull_latest_changes(repo_path):
        print("Beta build stopped during Git pull.")
        return False

    # --------------------------------------------------------
    # 3. Clean workspace
    # --------------------------------------------------------

    if not cop_clean(repo_path):
        print("Beta build stopped during COP clean.")
        return False

    # --------------------------------------------------------
    # 4. Repair workspace
    # --------------------------------------------------------

    if not cop_repair(repo_path):
        print("Beta build stopped during COP repair.")
        return False

    # --------------------------------------------------------
    # 5. Set extension versions
    # --------------------------------------------------------

    if not cop_set_versions(
        extension_groups,
        build_version,
        repo_path
    ):
        print("Beta build stopped during COP setversions.")
        return False

    # --------------------------------------------------------
    # 6. Review Git changes
    # --------------------------------------------------------

    changed_files = get_changed_files(repo_path)

    print("\nFiles changed after COP setversions:")

    if not changed_files:
        print("No changed files detected.")
        return False

    for changed_file in changed_files:
        print(changed_file)

    # --------------------------------------------------------
    # 7. User confirms Git changes
    # --------------------------------------------------------

    if not get_git_changes_confirmation():
        print("Beta build cancelled. Git changes were not approved.")
        return False

    # --------------------------------------------------------
    # 8. Stage version changes
    # --------------------------------------------------------

    if not stage_changes(repo_path):
        print("Beta build stopped while staging Git changes.")
        return False

    # --------------------------------------------------------
    # 9. Commit build version
    # --------------------------------------------------------

    if not commit_build_version(
        build_version,
        repo_path
    ):
        print("Beta build stopped while creating Git commit.")
        return False

    # --------------------------------------------------------
    # 10. Create Git tag
    # --------------------------------------------------------

    if not create_build_tag(
        build_version,
        repo_path
    ):
        print("Beta build stopped while creating Git tag.")
        return False

    # --------------------------------------------------------
    # 11. Build extensions
    # --------------------------------------------------------

    if not cop_make(
        extension_groups,
        repo_path
    ):
        print("Beta build failed during COP make.")
        return False

    # --------------------------------------------------------
    # 12. Upload Beta build
    # --------------------------------------------------------

    if not cop_upload(
        extension_groups,
        upload_name,
        repo_path
    ):
        print("Beta build failed during COP upload.")
        return False

    print("\n======================================================")
    print("              BETA BUILD SUCCESSFUL                   ")
    print("======================================================")
    print("Build Version :", build_version)
    print("Upload Name   :", upload_name)
    print("======================================================")

    return True