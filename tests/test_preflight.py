# ============================================================
# Project      : HNI Build Automation
# File         : test_preflight.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Tests for workflow/preflight.py: every check passes on a good
# repo, and each problem is caught with a clear message.
# Whether git/cop are installed is faked, so the tests also run
# on a PC without CET Developer.
#
# ============================================================

import os
import tempfile
import unittest
from unittest import mock

from tests.helpers import SandboxTestCase, git, remove_folder, write_file

import workflow.preflight as preflight

def fake_which(missing: str = ""):
    """shutil.which stand-in: every program is found, except the one named in missing."""
    def which(program):
        if program == missing:
            return None
        return f"C:\\fake\\{program}.exe"
    return which

class PreflightTests(SandboxTestCase):

    def run_checks(self, repo_path: str = None, missing: str = "") -> bool:
        with mock.patch.object(preflight.shutil, "which", fake_which(missing)):
            return preflight.run_preflight_checks(repo_path or self.sandbox.work)

    def test_good_repo_passes(self):
        self.assertTrue(self.run_checks())
        self.assertNotIn("[FAIL]", self.screen_text())

    def test_git_missing(self):
        self.assertFalse(self.run_checks(missing="git"))
        self.assertIn("git was not found", self.screen_text())

    def test_cop_missing(self):
        self.assertFalse(self.run_checks(missing="cop"))
        self.assertIn("cop was not found", self.screen_text())

    def test_missing_folder(self):
        self.assertFalse(self.run_checks(os.path.join(self.sandbox.root, "no_such_folder")))
        self.assertIn("HNI_BUILD_REPO_PATH", self.screen_text())

    def test_folder_that_is_not_a_repo(self):
        plain_folder = tempfile.mkdtemp(prefix="hni_build_plain_")
        self.addCleanup(remove_folder, plain_folder)
        self.assertFalse(self.run_checks(plain_folder))
        self.assertIn("is not a Git repo", self.screen_text())

    def test_unfinished_rebase(self):
        git_dir = git(self.sandbox.work, "rev-parse", "--absolute-git-dir")
        os.makedirs(os.path.join(git_dir, "rebase-merge"))
        self.assertFalse(self.run_checks())
        self.assertIn("git rebase --abort", self.screen_text())

    def test_uncommitted_changes_are_blocked_and_listed(self):
        self.sandbox.write_version("99.0.0.50")
        self.assertFalse(self.run_checks())
        self.assertIn("hbf/extension.xml", self.screen_text())
        self.assertIn("git stash", self.screen_text())

    def test_new_untracked_files_are_fine(self):
        write_file(os.path.join(self.sandbox.work, "notes.txt"), "not in Git\n")
        self.assertTrue(self.run_checks())

if __name__ == "__main__":
    unittest.main()
