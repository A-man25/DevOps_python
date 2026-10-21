# ============================================================
# Project      : HNI Build Automation
# File         : test_main.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Tests for main.py and the config files:
# - from the start to the build summary, with a fresh fetch
# - stopping early when a pre-flight check fails
# - Ctrl+C and unexpected errors end with a message and exit code 1
# - the workspace path setting
#
# ============================================================

import os
import unittest
from unittest import mock

from tests.helpers import QuietTestCase, SandboxTestCase, git

import main as tool_main
import workflow.preflight as preflight
import config.workspace_config as workspace_config
import config.dev_config as dev_config

def every_program_found(program):
    return f"C:\\fake\\{program}.exe"

class MainToSummaryTests(SandboxTestCase):

    def run_main(self, dev_mode: bool, *answers: str) -> int:
        self.answer(*answers)
        with mock.patch.object(tool_main, "get_repo_path", lambda: self.sandbox.work), \
             mock.patch.object(tool_main, "dev_mode", dev_mode), \
             mock.patch.object(preflight.shutil, "which", every_program_found):
            return tool_main.main()

    def test_dev_mode_counts_builds_made_on_another_pc(self):
        # Another PC made build 99.0.0.5; this PC does not know about it yet
        other = self.sandbox.clone_other_pc()
        git(other, "tag", "99.0.0.5")
        git(other, "push", "-q", "origin", "99.0.0.5")

        exit_code = self.run_main(True, "1", "4", "demo.build.99.0.0", "n")
        screen = self.screen_text()
        self.assertEqual(exit_code, 1)
        self.assertIn("Last Build       99.0.0.5", screen)
        self.assertIn("Next Version     99.0.0.6", screen)
        self.assertIn("Build cancelled.", screen)

    def test_release_mode_latest_branch(self):
        git(self.sandbox.work, "push", "-q", "origin", "HEAD:refs/heads/release/99.2.0")
        git(self.sandbox.work, "tag", "99.2.0.3")
        git(self.sandbox.work, "push", "-q", "origin", "99.2.0.3")

        exit_code = self.run_main(False, "1", "4", "l", "n")
        screen = self.screen_text()
        self.assertEqual(exit_code, 1)
        self.assertIn("origin/release/99.2.0", screen)
        self.assertIn("Next Version     99.2.0.4", screen)

    def test_failed_preflight_stops_before_any_question(self):
        self.sandbox.write_version("99.0.0.50")
        exit_code = self.run_main(True)
        self.assertEqual(exit_code, 1)
        self.assertIn("No uncommitted changes", self.screen_text())
        self.assertNotIn("SELECT BUILD TYPE", self.screen_text())

class RunTests(QuietTestCase):

    def test_unexpected_error_gives_message_log_and_exit_code_1(self):
        with mock.patch.object(tool_main, "main", side_effect=ValueError("something broke")):
            self.assertEqual(tool_main.run(), 1)
        self.assertIn("Unexpected error: something broke", self.screen_text())
        self.assertIn("ValueError: something broke", self.log_text())

    def test_ctrl_c_gives_exit_code_1(self):
        with mock.patch.object(tool_main, "main", side_effect=KeyboardInterrupt):
            self.assertEqual(tool_main.run(), 1)
        self.assertIn("Stopped with Ctrl+C.", self.screen_text())

    def test_finished_build_gives_exit_code_0(self):
        with mock.patch.object(tool_main, "main", return_value=0):
            self.assertEqual(tool_main.run(), 0)

class ConfigTests(unittest.TestCase):

    def test_workspace_path_from_windows_setting(self):
        with mock.patch.dict(os.environ, {"HNI_BUILD_REPO_PATH": " C:\\CetDev\\WPF\\extensions\\custom "}):
            self.assertEqual(workspace_config.get_repo_path(), "C:\\CetDev\\WPF\\extensions\\custom")

    def test_workspace_path_default(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("HNI_BUILD_REPO_PATH", None)
            self.assertEqual(workspace_config.get_repo_path(), workspace_config.DEFAULT_REPO_PATH)

    def test_dev_mode_is_true_or_false(self):
        self.assertIsInstance(dev_config.dev_mode, bool)

if __name__ == "__main__":
    unittest.main()
