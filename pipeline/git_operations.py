# ============================================================
# Project      : HNI Build Automation
# File         : git_operations.py
# Author       : Aman Rajesh Choudhari
# Created      : 14-Oct-2026
#
# Description:
# Handles Git-related operations required by the HNI build
# automation pipeline.
#
# Responsibilities:
# - Fetch release branches from the remote repository
# - Extract release version information from branch names
# - Convert version strings into comparable numeric tuples
# - Determine the latest available release branch
# - Checkout, pull, commit, tag and push the build version
#
# Checkout, pull, add, commit, tag and push run through
# run_command_live, which shows one live progress line.
# ============================================================

import subprocess

from pipeline.command_runner import run_command_live

def get_release_branches(repo_path:str) ->list[str]:
    git_command_list = ["git", "branch", "-r", "--list", "origin/release/*"]
    result = subprocess.run(git_command_list, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to return branches")
        print(result.stderr)
        return []
    
    branches = result.stdout.splitlines()
    return branches

def get_version_string_from_branch(branch: str) -> str:
    """Extracts the version string from a release branch name."""
    branch = branch.strip()
    return branch.split("/")[-1]

def version_string_to_tuple(version_str: str) -> tuple:
    version_str_list = version_str.split(".")
    version_num_list = []
    for val in version_str_list:
        version_num_list.append(int(val))

    return tuple(version_num_list)

def get_latest_release_branch(branches: list[str]) -> str:
    """Returns all remote HNI release branches from the repository."""
    latest_branch = None
    latest_version = None

    for this_branch in branches:
        version_str = get_version_string_from_branch(this_branch)
        version_tuple = version_string_to_tuple(version_str)

        if latest_version is None or version_tuple > latest_version:
            latest_version = version_tuple
            latest_branch = this_branch.strip()

    return latest_branch

def validate_release_branch(branch: str, release_branch_list: list[str]) -> str | None:
    branch = branch.strip().lower()
    if branch.startswith("origin/release/"):
        required_branch = branch
    elif branch.startswith("release/"):
        required_branch = "origin/" + branch
    else:
        required_branch = "origin/release/" + branch

    normalized_branch_list = []
    for this_branch in release_branch_list:
        normalized_branch_list.append(this_branch.strip().lower())

    if required_branch in normalized_branch_list:
        return required_branch

    return None

def get_git_tags(repo_path:str)->list[str]:
    git_command_list = ["git", "tag","--list"]
    result = subprocess.run( git_command_list, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to get Git tags.")
        print(result.stderr)
        return []

    return result.stdout.splitlines()

def checkout_release_branch(release_branch: str, repo_path: str) -> bool:
    # Convert remote branch name to local branch name
    if release_branch.startswith("origin/"):
        release_branch = release_branch.removeprefix("origin/")
        
    git_command = ["git", "checkout", release_branch]
    return run_command_live(git_command, repo_path, "GIT CHECKOUT", release_branch)

def pull_latest_changes(repo_path: str) -> bool:
    # --progress makes Git report progress even though its output is read by Python
    git_command = ["git", "pull", "--progress"]
    return run_command_live(git_command, repo_path, "GIT PULL")

def stage_changes(repo_path: str) -> bool:
    """Stages repository changes for the build version commit."""
    git_command = ["git", "add", "."]
    return run_command_live(git_command, repo_path, "GIT ADD")

def commit_build_version(build_version: str, repo_path: str) -> bool:
    """Creates the Git commit for the new build version."""
    git_command = ["git", "commit", "-m", build_version]
    return run_command_live(git_command, repo_path, "GIT COMMIT", build_version)

def create_build_tag(build_version: str, repo_path: str) -> bool:
    """Creates a Git tag for the build version."""
    git_command = ["git", "tag", build_version]
    return run_command_live(git_command, repo_path, "GIT TAG", build_version)

def get_changed_files(repo_path: str) -> list[str]:
    """Returns files currently modified in the Git working tree."""
    git_command = ["git", "status", "--short"]
    result = subprocess.run(git_command, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to get changed files.")
        print(result.stderr)
        return []

    return result.stdout.splitlines()

def push_changes(repo_path: str) -> bool:
    """Pushes the current branch commits to the remote repository."""
    git_command = ["git", "push", "--progress"]
    return run_command_live(git_command, repo_path, "GIT PUSH")

def push_build_tag(build_version: str, repo_path: str) -> bool:
    """Pushes the specific build tag to origin."""
    git_command = ["git", "push", "--progress", "origin", build_version]
    return run_command_live(git_command, repo_path, "GIT PUSH TAG", build_version)

# Test
def get_Test_branches(repo_path:str) ->list[str]:
    """Returns all remote test branches from the repository."""
    git_command_list = ["git", "branch", "-r", "--list", "origin/test/*"]
    result = subprocess.run(git_command_list, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to return branches")
        print(result.stderr)
        return []
    
    branches = result.stdout.splitlines()
    return branches


# Test
def validate_test_branch(branch: str, test_branch_list: list[str]) -> str | None:
    branch = branch.strip().lower()
    if branch.startswith("origin/test/"):
        required_branch = branch
    elif branch.startswith("test/"):
        required_branch = "origin/" + branch
    else:
        required_branch = "origin/test/" + branch

    # Return the branch name as it exists on remote (keeps original case)
    for this_branch in test_branch_list:
        this_branch = this_branch.strip()
        if this_branch.lower() == required_branch:
            return this_branch

    return None

# Test
def get_test_version_string_from_branch(branch: str) -> str:
    """Extracts the numeric version string from a test branch name.
    Example: origin/test/demo.build.17.5.0 -> 17.5.0
    """
    branch_name = get_version_string_from_branch(branch)
    version_str_list = []
    for val in branch_name.split("."):
        if val.isdigit():
            version_str_list.append(val)

    return ".".join(version_str_list)
