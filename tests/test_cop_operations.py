# ============================================================
# Project      : HNI Build Automation
# File         : test_cop_operations.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Tests for pipeline/cop_operations.py: every COP step runs the
# exact command expected, and compile errors are read and shown
# when cop make fails. COP itself is never run.
#
# ============================================================

import subprocess
import unittest
from unittest import mock

from tests.helpers import QuietTestCase

import pipeline.cop_operations as cop_operations

class CopCommandTests(QuietTestCase):

    def setUp(self):
        super().setUp()
        self.calls = []
        self.result = True
        patcher = mock.patch.object(cop_operations, "run_command_live", self.record)
        patcher.start()
        self.addCleanup(patcher.stop)

    def record(self, command, cwd, title, detail="", required_text=""):
        self.calls.append({"command": command, "cwd": cwd, "title": title,
                           "detail": detail, "required_text": required_text})
        return self.result

    def test_clean_and_repair(self):
        cop_operations.cop_clean("C:\\repo")
        cop_operations.cop_repair("C:\\repo")
        self.assertEqual(self.calls[0]["command"], ["cop", "clean"])
        self.assertEqual(self.calls[1]["command"], ["cop", "repair"])
        self.assertEqual(self.calls[0]["cwd"], "C:\\repo")

    def test_setversions_never_commits_or_tags(self):
        cop_operations.cop_set_versions(["[hon]", "[asi]"], "17.5.0.27", "C:\\repo")
        self.assertEqual(self.calls[0]["command"],
                         ["cop", "setversions", "[hon]", "[asi]", "/version=17.5.0.27", "/notag", "/nocommit"])

    def test_make_and_upload(self):
        cop_operations.cop_make(["[hbf]"], "C:\\repo")
        cop_operations.cop_upload(["[hbf]"], "17-5-0-27@BETA", "C:\\repo")
        self.assertEqual(self.calls[0]["command"], ["cop", "make", "[hbf]"])
        self.assertEqual(self.calls[1]["command"], ["cop", "upload", "[hbf]", "/uploadname=17-5-0-27@BETA"])

    def test_login_needs_coPs_success_message(self):
        cop_operations.cop_login("C:\\repo")
        self.assertEqual(self.calls[0]["command"], ["cop", "login"])
        self.assertEqual(self.calls[0]["required_text"], "Successfully logged in to MyConfigura")

    def test_failed_make_shows_the_compile_errors(self):
        self.result = False
        with mock.patch.object(cop_operations, "get_cop_make_errors", return_value=["hbf.cm(12): error: x"]):
            self.assertFalse(cop_operations.cop_make(["[hbf]"], "C:\\repo"))
        self.assertIn("Compile errors", self.screen_text())
        self.assertIn("hbf.cm(12): error: x", self.screen_text())

class CompileErrorReaderTests(unittest.TestCase):

    def test_heading_and_targets_are_left_out(self):
        cop_output = "\n".join([
            "cop make (using cop version 16.5.2621.0)",
            "Collecting items in workspace...",
            "COP make targets:",
            " 1) custom.hbf  C:\\BuildLogs\\custom.hbf.buildLog.cmtxt",
            " * Errors     custom.hbf     (worker1, time: 00:01:42)",
            "   hbf.cm(12): error: undefined variable 'x'",
        ])
        fake_result = subprocess.CompletedProcess(args=[], returncode=0, stdout=cop_output, stderr="")
        with mock.patch.object(cop_operations.subprocess, "run", return_value=fake_result) as run:
            errors = cop_operations.get_cop_make_errors(["[hbf]"], "C:\\repo")

        self.assertEqual(errors, ["* Errors     custom.hbf     (worker1, time: 00:01:42)",
                                  "hbf.cm(12): error: undefined variable 'x'"])
        self.assertIn("/printLastErrorsCompact", run.call_args.args[0])

    def test_cop_that_hangs_gives_a_message(self):
        with mock.patch.object(cop_operations.subprocess, "run", side_effect=subprocess.TimeoutExpired("cop", 300)):
            errors = cop_operations.get_cop_make_errors(["[hbf]"], "C:\\repo")
        self.assertIn("Could not read the errors", errors[0])

if __name__ == "__main__":
    unittest.main()
