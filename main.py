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

from models.enums import Build_Type


from ui.display import (
    begin_msg,
    show_build_summary,

    # Test
    show_dev_mode_msg
)

from ui.input_handler import (
    get_build_type,
    get_extension_list,
    get_build_confirmation
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
    get_git_tags,

    # Test
    get_test_version_string_from_branch
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

# Test
from config.dev_config import (
    dev_mode
)

def main():
    begin_msg()

    # Test
    if dev_mode:
        show_dev_mode_msg()

    repo_path = r"C:\CetDev\version16.5\extensions\custom"
    build_type = get_build_type()
    extension_list = get_extension_list()

    # Test
    release_branch = " "

    if not dev_mode:
        release_branch = get_required_release_branch(repo_path)
    else:
        release_branch = get_test_branch(repo_path)

    if release_branch is None:
        print("Could not determine release branch.")
        return

    # Test
    if not dev_mode:
        release_version = get_version_string_from_branch(release_branch)
    else:
        release_version = get_test_version_string_from_branch(release_branch)
        if not release_version:
            print("Could not determine version from test branch.")
            return

    git_tags = get_git_tags(repo_path)
    release_tags = get_release_build_tags(git_tags, release_version)
    latest_build_number = get_latest_build_number(release_tags)
    next_build_version = get_next_build_version(release_version, latest_build_number)
    cop_extension_groups = get_cop_extension_groups(extension_list)
    upload_name = get_beta_upload_name(next_build_version)

    show_build_summary(build_type, extension_list, release_branch, release_version, next_build_version)

    if not get_build_confirmation():
        print("\nBuild cancelled.")
        return
    if build_type == Build_Type.BETA:
        build_success = run_beta_build(repo_path, release_branch, cop_extension_groups, next_build_version, upload_name)
        if not build_success:
            print("\nBeta build failed.")
            return
    elif build_type == Build_Type.FIRST_AID:
        print("First Aid build is not implemented yet.")
        return
    elif build_type == Build_Type.PROJECT_BASED:
        print("Project Based build is not implemented yet.")
        return

if __name__ == "__main__":
    main()