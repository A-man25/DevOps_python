# ============================================================
# Project      : HNI Build Automation
# File         : main.py
# Author       : Aman Rajesh Choudhari
# Created      : 14-Oct-2026
#
# Description:
# Entry point for the HNI Build Automation tool.
# Coordinates the high-level build workflow.
#
# ============================================================

import sys

# The tool needs Python 3.10 or newer ("str | None" type hints).
# Checked before anything else is imported, so an old Python gets a clear message.
if sys.version_info < (3, 10):
    print("HNI Build Automation needs Python 3.10 or newer. This PC has Python " + sys.version.split()[0] + ".")
    sys.exit(1)

import traceback

from models.enums import Build_Type

from ui.colours import (
    enable_console_colours
)

from ui.display import (
    begin_msg,
    show_build_summary,
    show_connecting_msg,
    show_error_msg,
    show_error_details_msg,
    show_warning_msg,

    # Test
    show_dev_mode_msg
)

from ui.input_handler import (
    get_build_type,
    get_extension_list,
    get_build_confirmation
)

from workflow.preflight import (
    run_preflight_checks
)

from workflow.release_flow import (
    get_required_release_branch,

    # Test
    get_test_branch
)

from workflow.beta_build_flow import (
    run_beta_build
)

from pipeline.git_operations import (
    get_version_string_from_branch,
    is_numeric_version,
    fetch_from_server,
    get_git_tags,

    # Test
    get_test_version_string_from_branch
)

from pipeline.command_runner import (
    write_to_log
)

from pipeline.versioning import (
    get_release_build_tags,
    get_latest_build_number,
    get_next_build_version,
    get_beta_upload_name
)

from config.extension_config import (
    get_cop_extension_groups
)

from config.workspace_config import (
    get_repo_path
)

# Test
from config.dev_config import (
    dev_mode
)

def main() -> int:
    """Runs the tool. Returns 0 when a build finished, 1 when it stopped or was cancelled."""
    enable_console_colours()
    begin_msg()

    # Test
    if dev_mode:
        show_dev_mode_msg()

    repo_path = get_repo_path()

    # Check this PC first, so problems show up before any question is asked
    if not run_preflight_checks(repo_path):
        return 1

    # Latest branches and tags from the server, so the branch lists are
    # current and builds made on other PCs are counted
    show_connecting_msg()
    if not fetch_from_server(repo_path):
        show_error_msg("Could not get the latest branches and tags from the server. Check the network/VPN and try again.")
        return 1

    build_type = get_build_type()
    extension_list = get_extension_list()

    # Test
    release_branch = " "

    if not dev_mode:
        release_branch = get_required_release_branch(repo_path)
    else:
        release_branch = get_test_branch(repo_path)

    if release_branch is None:
        show_error_msg("Could not determine release branch.")
        return 1

    # Test
    if not dev_mode:
        release_version = get_version_string_from_branch(release_branch)
    else:
        release_version = get_test_version_string_from_branch(release_branch)

    if not release_version or not is_numeric_version(release_version):
        show_error_msg(f"Could not read a version number like 17.5.0 from {release_branch.strip()}.")
        return 1

    git_tags = get_git_tags(repo_path)
    release_tags = get_release_build_tags(git_tags, release_version)
    latest_build_number = get_latest_build_number(release_tags)
    next_build_version = get_next_build_version(release_version, latest_build_number)
    cop_extension_groups = get_cop_extension_groups(extension_list)
    upload_name = get_beta_upload_name(next_build_version)

    if latest_build_number > 0:
        last_build_version = f"{release_version}.{latest_build_number}"
    else:
        last_build_version = "none yet"

    show_build_summary(build_type, extension_list, release_branch, release_version, last_build_version, next_build_version)

    if not get_build_confirmation():
        show_warning_msg("Build cancelled.")
        return 1
    if build_type == Build_Type.BETA:
        # run_beta_build shows its own success / stopped banner
        build_success = run_beta_build(repo_path, release_branch, cop_extension_groups, next_build_version, upload_name)
        if not build_success:
            return 1
        return 0
    elif build_type == Build_Type.FIRST_AID:
        show_warning_msg("First Aid build is not implemented yet.")
        return 1
    elif build_type == Build_Type.PROJECT_BASED:
        show_warning_msg("Project Based build is not implemented yet.")
        return 1

    return 1

def run() -> int:
    """
    Starts the tool. Ctrl+C and unexpected errors end with a clear
    message (and the details in the log) instead of a Python traceback.
    """
    try:
        return main()
    except KeyboardInterrupt:
        show_warning_msg("Stopped with Ctrl+C.")
        return 1
    except Exception as error:
        log_path = write_to_log("UNEXPECTED ERROR\n" + traceback.format_exc())
        show_error_msg(f"Unexpected error: {error}")
        show_error_details_msg(log_path)
        return 1

if __name__ == "__main__":
    sys.exit(run())
