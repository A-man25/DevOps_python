# ============================================================
# Project      : HNI Build Automation
# File         : test_beta_build_flow.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Tests for workflow/beta_build_flow.py, the 16 build steps.
# Git is real (sandbox server + clone); COP and the login are
# faked. Each test checks what ends up on the server and that
# the workspace is left clean.
#
# ============================================================

import os
import unittest
from unittest import mock

from tests.helpers import SandboxTestCase, Sandbox, git, write_file

import workflow.beta_build_flow as flow

GENERATED_FILE = "hbf/_automaticSecurityDelegates.cm"

class BetaBuildFlowTests(SandboxTestCase):

    def setUp(self):
        super().setUp()
        self.make_ok = True
        self.during_make = None
        self.upload_results = []
        fakes = {
            "login_to_myconfigura": lambda repo: True,
            "cop_clean": lambda repo: True,
            "cop_repair": lambda repo: True,
            "cop_set_versions": self.fake_set_versions,
            "cop_make": self.fake_make,
            "cop_upload": self.fake_upload,
        }
        for name, fake in fakes.items():
            patcher = mock.patch.object(flow, name, fake)
            patcher.start()
            self.addCleanup(patcher.stop)

    # ---------------- fakes

    def fake_set_versions(self, groups, version, repo):
        self.sandbox.write_version(version)
        return True

    def fake_make(self, groups, repo):
        # A real build generates files like this one
        write_file(os.path.join(repo, GENERATED_FILE), "// generated, do not edit\n")
        if self.during_make:
            self.during_make()
        return self.make_ok

    def fake_upload(self, groups, upload_name, repo):
        if self.upload_results:
            return self.upload_results.pop(0)
        return True

    def run_build(self, version: str, *answers: str) -> bool:
        self.answer(*answers)
        return flow.run_beta_build(self.sandbox.work, Sandbox.RELEASE_BRANCH, ["[hbf]"],
                                   version, version.replace(".", "-") + "@BETA")

    def assert_nothing_happened(self, version: str):
        """The build stopped: nothing committed, nothing tagged, nothing pushed, workspace clean."""
        self.assertEqual(self.sandbox.head_subject(), "99.0.0.1")
        self.assertEqual(self.sandbox.read_version(), "<version>99.0.0.1</version>")
        self.assertNotIn(version, self.sandbox.local_tags())
        self.assertNotIn(version, self.sandbox.server_tags())
        self.assertTrue(self.sandbox.is_clean())

    # ---------------- tests

    def test_successful_build(self):
        self.assertTrue(self.run_build("99.0.0.2", "y", "y"))
        self.assertIn("99.0.0.2", self.sandbox.server_tags())
        self.assertEqual(self.sandbox.server_head_files(), [Sandbox.VERSION_FILE])
        self.assertNotIn(GENERATED_FILE, self.sandbox.server_files())
        self.assertTrue(self.sandbox.is_clean())
        self.assertIn("BETA BUILD SUCCESSFUL", self.screen_text())

    def test_failed_build_pushes_nothing_and_undoes_the_version(self):
        self.make_ok = False
        self.assertFalse(self.run_build("99.0.0.2", "y"))
        self.assert_nothing_happened("99.0.0.2")
        self.assertIn("99.0.0.2 is still free", self.screen_text())

    def test_cancel_at_review_undoes_the_version(self):
        self.assertFalse(self.run_build("99.0.0.2", "n"))
        self.assert_nothing_happened("99.0.0.2")

    def test_cancel_before_push_undoes_the_version(self):
        self.assertFalse(self.run_build("99.0.0.2", "y", "n"))
        self.assert_nothing_happened("99.0.0.2")

    def test_version_taken_on_another_pc_during_the_build(self):
        def other_pc_builds_same_version():
            other = self.sandbox.clone_other_pc()
            git(other, "tag", "99.0.0.2")
            git(other, "push", "-q", "origin", "99.0.0.2")
        self.during_make = other_pc_builds_same_version

        self.assertFalse(self.run_build("99.0.0.2", "y", "y"))
        self.assertEqual(self.sandbox.head_subject(), "99.0.0.1")
        self.assertTrue(self.sandbox.is_clean())
        self.assertIn("built on another PC meanwhile", self.screen_text())

    def test_failed_push_without_retry_removes_the_local_commit(self):
        with mock.patch.object(flow, "push_changes", lambda repo: False):
            self.assertFalse(self.run_build("99.0.0.2", "y", "y", "n"))
        self.assert_nothing_happened("99.0.0.2")

    def test_failed_push_then_retry_works(self):
        real_push = flow.push_changes
        attempts = []
        def push_fails_once(repo):
            attempts.append(1)
            return False if len(attempts) == 1 else real_push(repo)

        with mock.patch.object(flow, "push_changes", push_fails_once):
            self.assertTrue(self.run_build("99.0.0.2", "y", "y", "y"))
        self.assertEqual(len(attempts), 2)
        self.assertIn("99.0.0.2", self.sandbox.server_tags())

    def test_failed_upload_then_retry_works(self):
        self.upload_results = [False, True]
        self.assertTrue(self.run_build("99.0.0.2", "y", "y", "y"))
        self.assertIn("99.0.0.2", self.sandbox.server_tags())

    def test_failed_upload_without_retry_tells_how_to_upload_later(self):
        self.upload_results = [False]
        self.assertFalse(self.run_build("99.0.0.2", "y", "y", "n"))
        self.assertIn("99.0.0.2", self.sandbox.server_tags())
        self.assertIn("cop upload [hbf] /uploadname=99-0-0-2@BETA", self.screen_text())

    def test_leftover_local_commit_stops_the_build(self):
        self.sandbox.write_version("99.0.0.77")
        git(self.sandbox.work, "commit", "-q", "-am", "leftover from an old run")
        self.assertFalse(self.run_build("99.0.0.2"))
        self.assertEqual(self.sandbox.head_subject(), "leftover from an old run")
        self.assertIn("not on the server", self.screen_text())

    def test_version_already_in_files_stops_the_build(self):
        self.assertFalse(self.run_build("99.0.0.1"))
        self.assertIn("No version changes", self.screen_text())
        self.assertTrue(self.sandbox.is_clean())

if __name__ == "__main__":
    unittest.main()
