# ============================================================
# Project      : HNI Build Automation
# File         : test_release_flow.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Tests for workflow/release_flow.py: choosing the latest or a
# custom release branch, and a test branch in dev mode.
#
# ============================================================

import unittest

from tests.helpers import SandboxTestCase, Sandbox, git

from workflow.release_flow import (
    get_required_release_branch,
    get_test_branch
)

class ReleaseBranchChoiceTests(SandboxTestCase):

    def setUp(self):
        super().setUp()
        for branch in ["release/99.0.0", "release/99.10.0", "release/99.2.0"]:
            git(self.sandbox.work, "push", "-q", "origin", f"HEAD:refs/heads/{branch}")
        git(self.sandbox.work, "fetch", "-q", "origin")

    def test_latest_is_the_highest_version(self):
        self.answer("l")
        self.assertEqual(get_required_release_branch(self.sandbox.work), "origin/release/99.10.0")

    def test_custom_branch(self):
        self.answer("c", "99.2.0")
        self.assertEqual(get_required_release_branch(self.sandbox.work), "origin/release/99.2.0")

    def test_unknown_custom_branch_asks_again(self):
        self.answer("c", "98.0.0", "l")
        self.assertEqual(get_required_release_branch(self.sandbox.work), "origin/release/99.10.0")
        self.assertIn("Release branch does not exist.", self.screen_text())

    def test_wrong_answer_asks_again(self):
        self.answer("x", "l")
        self.assertEqual(get_required_release_branch(self.sandbox.work), "origin/release/99.10.0")

class NoReleaseBranchTests(SandboxTestCase):

    def test_no_release_branches(self):
        self.assertIsNone(get_required_release_branch(self.sandbox.work))
        self.assertIn("No release branches found.", self.screen_text())

class TestBranchChoiceTests(SandboxTestCase):

    def test_test_branch_by_short_name(self):
        self.answer("demo.build.99.0.0")
        self.assertEqual(get_test_branch(self.sandbox.work), Sandbox.RELEASE_BRANCH)

    def test_unknown_test_branch_asks_again(self):
        self.answer("nope", "test/demo.build.99.0.0")
        self.assertEqual(get_test_branch(self.sandbox.work), Sandbox.RELEASE_BRANCH)
        self.assertIn("Test branch does not exist.", self.screen_text())

if __name__ == "__main__":
    unittest.main()
