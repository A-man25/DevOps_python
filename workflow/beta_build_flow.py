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

import time

from pipeline.git_operations import (
    checkout_release_branch,
    pull_latest_changes,
    get_changed_files,
    stage_changes,
    commit_build_version,
    create_build_tag,
    push_changes,
    push_build_tag
)

from pipeline.cop_operations import (
    is_cop_login_set,
    set_cop_login,
    clear_cop_login,
    cop_login,
    cop_clean,
    cop_repair,
    cop_set_versions,
    cop_make,
    cop_upload
)

from ui.input_handler import (
    get_git_changes_confirmation,
    get_git_changes_push_confirmation,
    get_myconfigura_login,
    get_login_retry_confirmation
)

from ui.display import (
    show_step,
    show_changed_files,
    show_build_stopped,
    show_build_success
)

BETA_BUILD_STEPS = 15

def login_to_myconfigura(repo_path: str) -> bool:
    """
    Asks for the MyConfigura login once and passes it to COP.
    There is no saved login on this PC, so without it cop upload
    waits for a login it cannot ask for.
    Not asked if CETDEV_MC_USERNAME / CETDEV_MC_PASSWORD are
    already set in Windows.
    If the login fails, it offers to try again with another
    email and password.
    """
    if not is_cop_login_set():
        email, password = get_myconfigura_login()
        set_cop_login(email, password)

    if cop_login(repo_path):
        return True

    # Wrong email or password: forget it, so the next try asks again
    clear_cop_login()
    if get_login_retry_confirmation():
        return login_to_myconfigura(repo_path)

    return False

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
    start_time = time.monotonic()

    # --------------------------------------------------------
    # 0. Log in to MyConfigura (asked once, used by cop upload)
    # --------------------------------------------------------

    show_step(0, BETA_BUILD_STEPS, "Log in to MyConfigura")
    if not login_to_myconfigura(repo_path):
        show_build_stopped("Stopped during MyConfigura login.")
        return False

    # --------------------------------------------------------
    # 1. Checkout release branch
    # --------------------------------------------------------

    show_step(1, BETA_BUILD_STEPS, "Checkout release branch")
    if not checkout_release_branch(
        release_branch,
        repo_path
    ):
        show_build_stopped("Stopped during branch checkout.")
        return False

    # --------------------------------------------------------
    # 2. Pull latest source
    # --------------------------------------------------------

    show_step(2, BETA_BUILD_STEPS, "Pull latest source")
    if not pull_latest_changes(repo_path):
        show_build_stopped("Stopped during Git pull.")
        return False

    # --------------------------------------------------------
    # 3. Clean workspace
    # --------------------------------------------------------

    show_step(3, BETA_BUILD_STEPS, "Clean workspace")
    if not cop_clean(repo_path):
        show_build_stopped("Stopped during COP clean.")
        return False

    # --------------------------------------------------------
    # 4. Repair workspace
    # --------------------------------------------------------

    show_step(4, BETA_BUILD_STEPS, "Repair workspace")
    if not cop_repair(repo_path):
        show_build_stopped("Stopped during COP repair.")
        return False

    # --------------------------------------------------------
    # 5. Set extension versions
    # --------------------------------------------------------

    show_step(5, BETA_BUILD_STEPS, "Set extension versions")
    if not cop_set_versions(
        extension_groups,
        build_version,
        repo_path
    ):
        show_build_stopped("Stopped during COP setversions.")
        return False

    # --------------------------------------------------------
    # 6. Review Git changes
    # --------------------------------------------------------

    show_step(6, BETA_BUILD_STEPS, "Review Git changes")
    changed_files = get_changed_files(repo_path)
    if not changed_files:
        show_build_stopped("No changed files detected after COP setversions.")
        return False

    show_changed_files(changed_files)

    # --------------------------------------------------------
    # 7. User confirms Git changes
    # --------------------------------------------------------

    show_step(7, BETA_BUILD_STEPS, "Confirm Git changes")
    if not get_git_changes_confirmation():
        show_build_stopped("Cancelled. Git changes were not approved.")
        return False

    # --------------------------------------------------------
    # 8. Stage version changes
    # --------------------------------------------------------

    show_step(8, BETA_BUILD_STEPS, "Stage version changes")
    if not stage_changes(repo_path):
        show_build_stopped("Stopped while staging Git changes.")
        return False

    # --------------------------------------------------------
    # 9. Commit build version
    # --------------------------------------------------------

    show_step(9, BETA_BUILD_STEPS, "Commit build version")
    if not commit_build_version(
        build_version,
        repo_path
    ):
        show_build_stopped("Stopped while creating Git commit.")
        return False

    # --------------------------------------------------------
    # 10. Create Git tag
    # --------------------------------------------------------

    show_step(10, BETA_BUILD_STEPS, "Create Git tag")
    if not create_build_tag(
        build_version,
        repo_path
    ):
        show_build_stopped("Stopped while creating Git tag.")
        return False

    # --------------------------------------------------------
    # 11. User confirms Git push
    # --------------------------------------------------------

    show_step(11, BETA_BUILD_STEPS, "Confirm Git push")
    if not get_git_changes_push_confirmation():
        show_build_stopped("Cancelled. Git push was not approved.")
        return False

    # --------------------------------------------------------
    # 12. Push changes
    # --------------------------------------------------------

    show_step(12, BETA_BUILD_STEPS, "Push changes")
    if not push_changes(repo_path):
        show_build_stopped("Stopped, unable to push changes.")
        return False

    # --------------------------------------------------------
    # 13. Push build tag
    # --------------------------------------------------------

    show_step(13, BETA_BUILD_STEPS, "Push build tag")
    if not push_build_tag(build_version, repo_path):
        show_build_stopped("Stopped, unable to push build tag.")
        return False

    # --------------------------------------------------------
    # 14. Build extensions
    # --------------------------------------------------------

    show_step(14, BETA_BUILD_STEPS, "Build extensions")
    if not cop_make(
        extension_groups,
        repo_path
    ):
        show_build_stopped("Failed during COP make.")
        return False

    # --------------------------------------------------------
    # 15. Upload Beta build
    # --------------------------------------------------------

    show_step(15, BETA_BUILD_STEPS, "Upload Beta build")
    if not cop_upload(
        extension_groups,
        upload_name,
        repo_path
    ):
        show_build_stopped("Failed during COP upload.")
        return False

    show_build_success(build_version, upload_name, time.monotonic() - start_time)

    return True
