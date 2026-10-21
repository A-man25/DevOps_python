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
# - Build selected extensions
# - Commit, tag and push the build version (only after the build works)
# - Upload the Beta build
#
# Safety rules:
# - Nothing reaches the server until the build has worked.
# - If the build stops before the push, the version changes are
#   undone, so the workspace is clean and the version is still free.
# - Steps that talk to the server (push, upload) can be tried again.
#
# ============================================================

import time

from pipeline.git_operations import (
    checkout_release_branch,
    pull_latest_changes,
    count_unpushed_commits,
    get_changed_files,
    get_modified_files,
    undo_version_changes,
    is_tag_on_server,
    stage_files,
    commit_build_version,
    create_build_tag,
    push_changes,
    push_build_tag,
    undo_local_build_commit
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
    get_remember_login_confirmation,
    get_login_retry_confirmation,
    get_retry_confirmation
)

from ui.display import (
    show_step,
    show_changed_files,
    show_build_stopped,
    show_build_success,
    show_saved_login_msg,
    show_login_saved_msg,
    show_saved_login_removed_msg,
    show_version_free_msg
)

from utils.credential_store import (
    save_login,
    load_saved_login,
    delete_saved_login
)

BETA_BUILD_STEPS = 16

def login_to_myconfigura(repo_path: str) -> bool:
    """
    Gets the MyConfigura login and passes it to COP.
    COP logs in again for every command, so cop upload needs it
    every build.

    Where the login comes from, in this order:
    1. CETDEV_MC_USERNAME / CETDEV_MC_PASSWORD already set in Windows
    2. The login saved on this PC (Windows Credential Manager)
    3. Asked now. After it works, the user may save it.

    The login is checked with cop login. If it fails, a saved
    login is removed and the user may try again.
    """
    login_source = "windows"
    if not is_cop_login_set():
        saved_login = load_saved_login()
        if saved_login is not None:
            login_source = "saved"
            email, password = saved_login
            show_saved_login_msg(email)
        else:
            login_source = "typed"
            email, password = get_myconfigura_login()
        set_cop_login(email, password)

    if cop_login(repo_path):
        # Offer to remember a typed login, now that it is known to work
        if login_source == "typed" and get_remember_login_confirmation():
            show_login_saved_msg(save_login(email, password))
        return True

    # Wrong email or password: forget it, so the next try asks again
    clear_cop_login()
    if login_source == "saved":
        delete_saved_login()
        show_saved_login_removed_msg()

    if get_login_retry_confirmation():
        return login_to_myconfigura(repo_path)

    return False

def run_with_retry(step_name: str, step_function, *step_args) -> bool:
    """
    Runs a step that talks to the server (push, upload). If it fails,
    for example because of a network problem, it can be tried again
    instead of losing the whole build.
    """
    while True:
        if step_function(*step_args):
            return True
        if not get_retry_confirmation(step_name):
            return False

def stop_and_undo(version_files: list[str], repo_path: str, reason: str) -> bool:
    """Undoes the version changes (nothing was committed yet) and stops the build."""
    undo_version_changes(version_files, repo_path)
    show_build_stopped(reason)
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
    # 0. Log in to MyConfigura (saved on this PC, or asked)
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
        show_build_stopped("Stopped during Git pull. If the local branch has commits the server does not have, see the message above.")
        return False

    # Local commits the server does not have (e.g. from an earlier run whose
    # push failed) would be pushed together with this build
    unpushed_commits = count_unpushed_commits(release_branch, repo_path)
    if unpushed_commits == -1:
        show_build_stopped("Could not compare the local branch with the server.")
        return False
    if unpushed_commits > 0:
        show_build_stopped(f"The local branch has {unpushed_commits} commit(s) that are not on the server. "
                           f"See them with: git log origin/{release_branch.removeprefix('origin/')}..HEAD")
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
    set_versions_ok = cop_set_versions(
        extension_groups,
        build_version,
        repo_path
    )

    # From here on, these are the files the build commit will contain
    version_files = get_modified_files(repo_path)
    if not set_versions_ok:
        return stop_and_undo(version_files, repo_path, "Stopped during COP setversions.")

    # --------------------------------------------------------
    # 6. Review Git changes
    # --------------------------------------------------------

    show_step(6, BETA_BUILD_STEPS, "Review Git changes")
    show_changed_files(get_changed_files(repo_path))
    if not version_files:
        show_build_stopped(f"No version changes after COP setversions (files already at {build_version}?).")
        return False

    # --------------------------------------------------------
    # 7. User confirms Git changes
    # --------------------------------------------------------

    show_step(7, BETA_BUILD_STEPS, "Confirm Git changes")
    if not get_git_changes_confirmation():
        return stop_and_undo(version_files, repo_path, "Cancelled. Git changes were not approved.")

    # --------------------------------------------------------
    # 8. Build extensions (before anything is committed or pushed)
    # --------------------------------------------------------

    show_step(8, BETA_BUILD_STEPS, "Build extensions")
    if not cop_make(
        extension_groups,
        repo_path
    ):
        return stop_and_undo(version_files, repo_path,
                             f"Failed during COP make. Nothing was committed or pushed, {build_version} is still free.")

    # --------------------------------------------------------
    # 9. User confirms commit and push
    # --------------------------------------------------------

    show_step(9, BETA_BUILD_STEPS, "Confirm commit and push")
    if not get_git_changes_push_confirmation():
        return stop_and_undo(version_files, repo_path, "Cancelled. Commit and push were not approved.")

    # --------------------------------------------------------
    # 10. Check the version is still free on the server
    #     (someone may have built it on another PC meanwhile)
    # --------------------------------------------------------

    show_step(10, BETA_BUILD_STEPS, "Check the version is still free")
    tag_on_server = is_tag_on_server(build_version, repo_path)
    if tag_on_server is None:
        return stop_and_undo(version_files, repo_path,
                             f"Could not reach the server to check {build_version}. Check the network/VPN and run again.")
    if tag_on_server:
        return stop_and_undo(version_files, repo_path,
                             f"{build_version} was built on another PC meanwhile. Run the tool again; it will pick the next number.")
    show_version_free_msg(build_version)

    # --------------------------------------------------------
    # 11. Stage version changes (exactly the reviewed files)
    # --------------------------------------------------------

    show_step(11, BETA_BUILD_STEPS, "Stage version changes")
    if not stage_files(version_files, repo_path):
        return stop_and_undo(version_files, repo_path, "Stopped while staging Git changes.")

    # --------------------------------------------------------
    # 12. Commit build version
    # --------------------------------------------------------

    show_step(12, BETA_BUILD_STEPS, "Commit build version")
    if not commit_build_version(
        build_version,
        repo_path
    ):
        return stop_and_undo(version_files, repo_path, "Stopped while creating Git commit.")

    # --------------------------------------------------------
    # 13. Create Git tag
    # --------------------------------------------------------

    show_step(13, BETA_BUILD_STEPS, "Create Git tag")
    if not create_build_tag(
        build_version,
        repo_path
    ):
        undo_local_build_commit(build_version, release_branch, repo_path)
        show_build_stopped("Stopped while creating Git tag. The local commit was undone.")
        return False

    # --------------------------------------------------------
    # 14. Push changes
    # --------------------------------------------------------

    show_step(14, BETA_BUILD_STEPS, "Push changes")
    if not run_with_retry("Git push", push_changes, repo_path):
        if undo_local_build_commit(build_version, release_branch, repo_path):
            show_build_stopped(f"Stopped, unable to push changes. The local commit and tag were undone, {build_version} is still free.")
        else:
            show_build_stopped("Stopped, unable to push changes. The local commit and tag are still on this PC.")
        return False

    # --------------------------------------------------------
    # 15. Push build tag
    # --------------------------------------------------------

    show_step(15, BETA_BUILD_STEPS, "Push build tag")
    if not run_with_retry("Git push tag", push_build_tag, build_version, repo_path):
        show_build_stopped(f"Stopped, unable to push the build tag. The commit is on the server. "
                           f"Push the tag later with: git push origin {build_version}")
        return False

    # --------------------------------------------------------
    # 16. Upload Beta build
    # --------------------------------------------------------

    show_step(16, BETA_BUILD_STEPS, "Upload Beta build")
    if not run_with_retry("COP upload", cop_upload, extension_groups, upload_name, repo_path):
        show_build_stopped(f"Failed during COP upload. Upload later with: "
                           f"cop upload {' '.join(extension_groups)} /uploadname={upload_name}")
        return False

    show_build_success(build_version, upload_name, time.monotonic() - start_time)

    return True
