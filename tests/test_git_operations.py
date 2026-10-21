# ============================================================
# Project      : HNI Build Automation
# File         : test_git_operations.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Tests for pipeline/git_operations.py with real Git, in a
# sandbox (a fake server repo and a working clone).
#
# ============================================================

import os
import unittest

from tests.helpers import SandboxTestCase, Sandbox, git, write_file

from pipeline.git_operations import (
    is_git_repo,
    has_origin_remote,
    has_git_identity,
    get_operation_in_progress,
    get_uncommitted_tracked_files,
    fetch_from_server,
    get_release_branches,
    get_Test_branches,
    get_git_tags,
    is_tag_on_server,
    checkout_release_branch,
    pull_latest_changes,
    count_unpushed_commits,
    get_changed_files,
    get_modified_files,
    undo_version_changes,
    stage_files,
    commit_build_version,
    create_build_tag,
    push_changes,
    push_build_tag,
    undo_local_build_commit
)

class RepoCheckTests(SandboxTestCase):

    def test_repo_checks_on_a_good_repo(self):
        work = self.sandbox.work
        self.assertTrue(is_git_repo(work))
        self.assertTrue(has_origin_remote(work))
        self.assertTrue(has_git_identity(work))
        self.assertEqual(get_operation_in_progress(work), "")
        self.assertEqual(get_uncommitted_tracked_files(work), [])

    def test_plain_folder_is_not_a_repo(self):
        self.assertFalse(is_git_repo(self.sandbox.root))

    def test_unfinished_merge_is_found(self):
        git_dir = git(self.sandbox.work, "rev-parse", "--absolute-git-dir")
        write_file(os.path.join(git_dir, "MERGE_HEAD"), "0" * 40 + "\n")
        self.assertEqual(get_operation_in_progress(self.sandbox.work), "merge")

    def test_uncommitted_changes_count_but_new_files_do_not(self):
        write_file(os.path.join(self.sandbox.work, "notes.txt"), "new file\n")
        self.assertEqual(get_uncommitted_tracked_files(self.sandbox.work), [])
        self.sandbox.write_version("99.0.0.50")
        self.assertEqual(len(get_uncommitted_tracked_files(self.sandbox.work)), 1)

class ServerTests(SandboxTestCase):

    def test_fetch_gets_tags_and_branches_made_on_another_pc(self):
        other = self.sandbox.clone_other_pc()
        git(other, "checkout", "-q", "-b", "release/99.1.0")
        git(other, "push", "-q", "origin", "release/99.1.0")
        git(other, "tag", "99.0.0.7")
        git(other, "push", "-q", "origin", "99.0.0.7")

        self.assertNotIn("99.0.0.7", get_git_tags(self.sandbox.work))
        self.assertTrue(fetch_from_server(self.sandbox.work))
        self.assertIn("99.0.0.7", get_git_tags(self.sandbox.work))
        self.assertIn("origin/release/99.1.0", [b.strip() for b in get_release_branches(self.sandbox.work)])
        self.assertIn(Sandbox.RELEASE_BRANCH, [b.strip() for b in get_Test_branches(self.sandbox.work)])

    def test_tag_on_server(self):
        self.assertTrue(is_tag_on_server("99.0.0.1", self.sandbox.work))
        self.assertFalse(is_tag_on_server("99.0.0.2", self.sandbox.work))

    def test_tag_check_without_server_is_unknown(self):
        git(self.sandbox.work, "remote", "set-url", "origin", os.path.join(self.sandbox.root, "missing.git"))
        self.assertIsNone(is_tag_on_server("99.0.0.1", self.sandbox.work))

class PullTests(SandboxTestCase):

    def test_pull_brings_new_commits(self):
        other = self.sandbox.clone_other_pc()
        self.sandbox.write_version("99.0.0.2", other)
        git(other, "commit", "-q", "-am", "99.0.0.2")
        git(other, "push", "-q")

        self.assertTrue(checkout_release_branch(Sandbox.RELEASE_BRANCH, self.sandbox.work))
        self.assertTrue(pull_latest_changes(self.sandbox.work))
        self.assertEqual(self.sandbox.head_subject(), "99.0.0.2")

    def test_pull_refuses_to_merge_when_branches_differ(self):
        other = self.sandbox.clone_other_pc()
        self.sandbox.write_version("99.0.0.2", other)
        git(other, "commit", "-q", "-am", "from the other PC")
        git(other, "push", "-q")

        self.sandbox.write_version("99.0.0.3")
        git(self.sandbox.work, "commit", "-q", "-am", "local only")
        self.assertFalse(pull_latest_changes(self.sandbox.work))
        self.assertEqual(self.sandbox.head_subject(), "local only")

    def test_unpushed_commits_are_counted(self):
        self.assertEqual(count_unpushed_commits(Sandbox.RELEASE_BRANCH, self.sandbox.work), 0)
        self.sandbox.write_version("99.0.0.9")
        git(self.sandbox.work, "commit", "-q", "-am", "not pushed")
        self.assertEqual(count_unpushed_commits(Sandbox.RELEASE_BRANCH, self.sandbox.work), 1)

class VersionFileTests(SandboxTestCase):

    def test_modified_files_and_undo(self):
        self.sandbox.write_version("99.0.0.2")
        write_file(os.path.join(self.sandbox.work, "hbf", "generated.cm"), "// generated\n")
        self.assertEqual(get_modified_files(self.sandbox.work), [Sandbox.VERSION_FILE])
        self.assertEqual(len(get_changed_files(self.sandbox.work)), 2)

        self.assertTrue(undo_version_changes([Sandbox.VERSION_FILE], self.sandbox.work))
        self.assertEqual(self.sandbox.read_version(), "<version>99.0.0.1</version>")

    def test_undo_with_no_files_does_nothing(self):
        self.assertTrue(undo_version_changes([], self.sandbox.work))
        self.assertNotIn("GIT RESTORE", self.screen_text())

    def test_stage_only_the_given_files(self):
        write_file(os.path.join(self.sandbox.work, "other.txt"), "tracked\n")
        git(self.sandbox.work, "add", "other.txt")
        git(self.sandbox.work, "commit", "-q", "-m", "add other.txt")
        self.sandbox.write_version("99.0.0.2")
        write_file(os.path.join(self.sandbox.work, "other.txt"), "changed by the build\n")

        self.assertTrue(stage_files([Sandbox.VERSION_FILE], self.sandbox.work))
        staged = git(self.sandbox.work, "diff", "--cached", "--name-only").split()
        self.assertEqual(staged, [Sandbox.VERSION_FILE])

class CommitPushTests(SandboxTestCase):

    def make_build_commit(self, version: str):
        self.sandbox.write_version(version)
        self.assertTrue(stage_files([Sandbox.VERSION_FILE], self.sandbox.work))
        self.assertTrue(commit_build_version(version, self.sandbox.work))
        self.assertTrue(create_build_tag(version, self.sandbox.work))

    def test_commit_tag_and_push(self):
        self.make_build_commit("99.0.0.2")
        self.assertTrue(push_changes(self.sandbox.work))
        self.assertTrue(push_build_tag("99.0.0.2", self.sandbox.work))
        self.assertIn("99.0.0.2", self.sandbox.server_tags())
        self.assertEqual(git(self.sandbox.server, "log", "-1", "--format=%s", Sandbox.BRANCH), "99.0.0.2")

    def test_undo_local_build_commit_that_was_not_pushed(self):
        self.make_build_commit("99.0.0.2")
        self.assertTrue(undo_local_build_commit("99.0.0.2", Sandbox.RELEASE_BRANCH, self.sandbox.work))
        self.assertEqual(self.sandbox.head_subject(), "99.0.0.1")
        self.assertNotIn("99.0.0.2", self.sandbox.local_tags())
        self.assertTrue(self.sandbox.is_clean())

    def test_undo_refuses_when_commit_is_already_on_server(self):
        self.make_build_commit("99.0.0.2")
        self.assertTrue(push_changes(self.sandbox.work))
        self.assertFalse(undo_local_build_commit("99.0.0.2", Sandbox.RELEASE_BRANCH, self.sandbox.work))
        self.assertEqual(self.sandbox.head_subject(), "99.0.0.2")

    def test_undo_refuses_when_last_commit_is_not_the_build(self):
        self.sandbox.write_version("99.0.0.2")
        git(self.sandbox.work, "commit", "-q", "-am", "someone's work")
        self.assertFalse(undo_local_build_commit("99.0.0.2", Sandbox.RELEASE_BRANCH, self.sandbox.work))
        self.assertEqual(self.sandbox.head_subject(), "someone's work")

if __name__ == "__main__":
    unittest.main()
