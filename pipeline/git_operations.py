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
# - Check the repo is safe to build from (pre-flight checks)
# - Undo the tool's own changes when a build stops
#
# Steps that change something run through run_command_live,
# which shows one live progress line. Quick read-only commands
# use run_git.
# ============================================================

import os
import subprocess

from pipeline.command_runner import run_command_live

def run_git(git_args: list[str], repo_path: str, timeout: int | None = None) -> subprocess.CompletedProcess:
    """
    Runs a quick Git command and returns its result.
    Git prints UTF-8, so the text is read as UTF-8 (odd characters are
    replaced instead of crashing the tool).
    GIT_TERMINAL_PROMPT=0: Git never waits for a password in the console here.
    """
    git_env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    return subprocess.run(["git", *git_args], cwd=repo_path, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=git_env, timeout=timeout)

# ------------------------------------------------------------
# Pre-flight checks
# ------------------------------------------------------------

def is_git_repo(repo_path: str) -> bool:
    result = run_git(["rev-parse", "--is-inside-work-tree"], repo_path)
    return result.returncode == 0 and result.stdout.strip() == "true"

def has_origin_remote(repo_path: str) -> bool:
    return run_git(["remote", "get-url", "origin"], repo_path).returncode == 0

def has_git_identity(repo_path: str) -> bool:
    """Git needs a name and email to make the build commit."""
    name = run_git(["config", "user.name"], repo_path).stdout.strip()
    email = run_git(["config", "user.email"], repo_path).stdout.strip()
    return bool(name) and bool(email)

def get_operation_in_progress(repo_path: str) -> str:
    """Returns the name of an unfinished merge/rebase/cherry-pick/revert, or "" if none."""
    git_dir = run_git(["rev-parse", "--absolute-git-dir"], repo_path).stdout.strip()
    checks = [("MERGE_HEAD", "merge"), ("rebase-merge", "rebase"), ("rebase-apply", "rebase"),
              ("CHERRY_PICK_HEAD", "cherry-pick"), ("REVERT_HEAD", "revert")]
    for file_name, operation in checks:
        if git_dir and os.path.exists(os.path.join(git_dir, file_name)):
            return operation

    return ""

def get_uncommitted_tracked_files(repo_path: str) -> list[str]:
    """Tracked files with changes that are not committed. New (untracked) files are ignored."""
    result = run_git(["status", "--short", "--untracked-files=no"], repo_path)
    return result.stdout.splitlines()

def fetch_from_server(repo_path: str) -> bool:
    """
    Downloads the latest branches and tags from the server, so the branch
    lists are current and builds made on other PCs are counted when the
    next version is worked out.
    --prune : forgets branches that were deleted on the server
    --tags  : downloads every tag (build number)
    --force : if a local tag differs from the server's, the server wins
    """
    git_command = ["git", "fetch", "origin", "--prune", "--tags", "--force", "--progress"]
    return run_command_live(git_command, repo_path, "GIT FETCH")

# ------------------------------------------------------------
# Branches and versions
# ------------------------------------------------------------

def get_release_branches(repo_path:str) ->list[str]:
    result = run_git(["branch", "-r", "--list", "origin/release/*"], repo_path)
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

def is_numeric_version(version_str: str) -> bool:
    """True for versions like 17.5.0 (only numbers and dots)."""
    version_str_list = version_str.split(".")
    for val in version_str_list:
        if not val.isdigit():
            return False

    return True

def version_string_to_tuple(version_str: str) -> tuple:
    version_str_list = version_str.split(".")
    version_num_list = []
    for val in version_str_list:
        version_num_list.append(int(val))

    return tuple(version_num_list)

def get_latest_release_branch(branches: list[str]) -> str:
    """
    Returns the release branch with the highest version.
    Branches whose name is not a plain version (e.g. release/17.5.0-hotfix)
    are skipped instead of crashing the tool.
    """
    latest_branch = None
    latest_version = None

    for this_branch in branches:
        version_str = get_version_string_from_branch(this_branch)
        if not is_numeric_version(version_str):
            continue

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

    # Return the branch name as it exists on remote (keeps original case)
    for this_branch in release_branch_list:
        this_branch = this_branch.strip()
        if this_branch.lower() == required_branch:
            return this_branch

    return None

def get_git_tags(repo_path:str)->list[str]:
    result = run_git(["tag", "--list"], repo_path)
    if result.returncode != 0:
        print("Failed to get Git tags.")
        print(result.stderr)
        return []

    return result.stdout.splitlines()

def is_tag_on_server(tag: str, repo_path: str) -> bool | None:
    """True if the tag exists on the server, False if not, None if the server could not be asked."""
    try:
        result = run_git(["ls-remote", "--tags", "origin", f"refs/tags/{tag}"], repo_path, timeout=60)
    except subprocess.TimeoutExpired:
        return None

    if result.returncode != 0:
        return None

    return bool(result.stdout.strip())

# ------------------------------------------------------------
# Build steps
# ------------------------------------------------------------

def checkout_release_branch(release_branch: str, repo_path: str) -> bool:
    # Convert remote branch name to local branch name
    if release_branch.startswith("origin/"):
        release_branch = release_branch.removeprefix("origin/")

    git_command = ["git", "checkout", release_branch]
    return run_command_live(git_command, repo_path, "GIT CHECKOUT", release_branch)

def pull_latest_changes(repo_path: str) -> bool:
    """
    --ff-only : only moves the branch forward. If the local branch has commits
                the server does not have, Git stops instead of making a merge commit.
    --progress: makes Git report progress even though its output is read by Python
    """
    git_command = ["git", "pull", "--ff-only", "--progress"]
    return run_command_live(git_command, repo_path, "GIT PULL")

def count_unpushed_commits(release_branch: str, repo_path: str) -> int:
    """Number of local commits on the branch that are not on the server (-1 if unknown)."""
    if not release_branch.startswith("origin/"):
        release_branch = "origin/" + release_branch

    result = run_git(["rev-list", "--count", f"{release_branch}..HEAD"], repo_path)
    if result.returncode != 0 or not result.stdout.strip().isdigit():
        return -1

    return int(result.stdout.strip())

def get_changed_files(repo_path: str) -> list[str]:
    """Returns files currently modified in the Git working tree (git status --short, for showing)."""
    result = run_git(["status", "--short"], repo_path)
    if result.returncode != 0:
        print("Failed to get changed files.")
        print(result.stderr)
        return []

    return result.stdout.splitlines()

def get_modified_files(repo_path: str) -> list[str]:
    """
    Returns the exact paths of tracked files changed in the working folder.
    Used to commit (or undo) exactly the files cop setversions changed.
    """
    result = run_git(["diff", "--name-only", "-z"], repo_path)
    modified_files = []
    for path in result.stdout.split("\0"):
        if path:
            modified_files.append(path)

    return modified_files

def undo_version_changes(version_files: list[str], repo_path: str) -> bool:
    """
    Puts the files cop setversions changed back as they are in the last commit,
    so a stopped build leaves the workspace clean and the version is free again.
    """
    if not version_files:
        return True

    git_command = ["git", "checkout", "HEAD", "--", *version_files]
    return run_command_live(git_command, repo_path, "GIT RESTORE", "version changes undone")

def stage_files(version_files: list[str], repo_path: str) -> bool:
    """
    Stages exactly the files that were reviewed after cop setversions.
    Nothing else is committed: not new files a build generates (like
    hbf/_automaticSecurityDelegates.cm), and not other changes a build makes.
    """
    git_command = ["git", "add", "--", *version_files]
    return run_command_live(git_command, repo_path, "GIT ADD")

def commit_build_version(build_version: str, repo_path: str) -> bool:
    """Creates the Git commit for the new build version."""
    git_command = ["git", "commit", "-m", build_version]
    return run_command_live(git_command, repo_path, "GIT COMMIT", build_version)

def create_build_tag(build_version: str, repo_path: str) -> bool:
    """Creates a Git tag for the build version."""
    git_command = ["git", "tag", build_version]
    return run_command_live(git_command, repo_path, "GIT TAG", build_version)

def push_changes(repo_path: str) -> bool:
    """Pushes the current branch commits to the same branch on the server."""
    git_command = ["git", "push", "--progress", "origin", "HEAD"]
    return run_command_live(git_command, repo_path, "GIT PUSH")

def push_build_tag(build_version: str, repo_path: str) -> bool:
    """Pushes the specific build tag to origin."""
    git_command = ["git", "push", "--progress", "origin", build_version]
    return run_command_live(git_command, repo_path, "GIT PUSH TAG", build_version)

def undo_local_build_commit(build_version: str, release_branch: str, repo_path: str) -> bool:
    """
    Removes the build commit and tag made on this PC when they could not be
    pushed, so the next run starts clean and the version is free again.

    Safety: only done when the last commit is the build commit (its message is
    the version) and the server does not have it.
    """
    subject = run_git(["log", "-1", "--format=%s"], repo_path).stdout.strip()
    if subject != build_version:
        return False

    branch_name = release_branch.removeprefix("origin/")
    head = run_git(["rev-parse", "HEAD"], repo_path).stdout.strip()
    try:
        remote = run_git(["ls-remote", "origin", f"refs/heads/{branch_name}"], repo_path, timeout=60)
    except subprocess.TimeoutExpired:
        return False

    if remote.returncode != 0 or head in remote.stdout:
        return False

    run_git(["tag", "-d", build_version], repo_path)
    return run_git(["reset", "--hard", "HEAD~1"], repo_path).returncode == 0

# ------------------------------------------------------------
# Test branches (dev mode)
# ------------------------------------------------------------

# Test
def get_Test_branches(repo_path:str) ->list[str]:
    """Returns all remote test branches from the repository."""
    result = run_git(["branch", "-r", "--list", "origin/test/*"], repo_path)
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
