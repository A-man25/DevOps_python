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
# ============================================================

import subprocess

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
    result = subprocess.run(git_command, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to checkout release branch.")
        print(result.stderr)
        return False

    print(f"Successfully checked out: {release_branch}")

    return True

def pull_latest_changes(repo_path: str) -> bool:
    git_command = ["git", "pull"]
    result = subprocess.run(git_command, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to pull latest changes.")
        print(result.stderr)
        return False
    print("Successfully pulled latest changes.")
    return True

def stage_changes(repo_path: str) -> bool:
    """Stages repository changes for the build version commit."""
    git_command = ["git", "add", "."]
    result = subprocess.run(git_command, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to stage Git changes.")
        print(result.stderr)
        return False

    print("Git changes staged successfully.")
    return True

def commit_build_version(build_version: str, repo_path: str) -> bool:
    """Creates the Git commit for the new build version."""
    git_command = ["git", "commit", "-m", build_version]
    result = subprocess.run(git_command, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to commit build version.")
        print(result.stderr)
        return False

    print(f"Git commit created: {build_version}")
    return True

def create_build_tag(build_version: str, repo_path: str) -> bool:
    """Creates a Git tag for the build version."""
    git_command = ["git", "tag", build_version]
    result = subprocess.run(git_command, cwd=repo_path, capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to create Git tag.")
        print(result.stderr)
        return False

    print(f"Git tag created: {build_version}")
    return True

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
   git_command = ["git", "push"]
   print("\nExecuting command:")
   print(" ".join(git_command))
   result = subprocess.run(git_command, cwd=repo_path, text=True)
   if result.returncode != 0:
       print("Failed to push branch changes.")
       return False
   print("Branch changes pushed successfully.")
   return True

def push_build_tag(build_version: str, repo_path: str) -> bool:
   """Pushes the specific build tag to origin."""
   git_command = ["git", "push", "origin", build_version]
   print("\nExecuting command:")
   print(" ".join(git_command))
   result = subprocess.run(git_command, cwd=repo_path, text=True)
   if result.returncode != 0:
       print(f"Failed to push Git tag: {build_version}")
       return False
   print(f"Git tag pushed successfully: {build_version}")
   return True