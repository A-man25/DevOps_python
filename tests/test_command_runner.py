# ============================================================
# Project      : HNI Build Automation
# File         : test_command_runner.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Tests for pipeline/command_runner.py (run_command_live).
# Small Python scripts stand in for git and cop, so every case
# (failures, COP's messages, questions, Ctrl+C) can be tried
# in seconds without a real build.
#
# ============================================================

import os
import signal
import sys
import tempfile
import threading
import time
import unittest
import _thread

from tests.helpers import QuietTestCase, remove_folder, write_file

from pipeline.command_runner import run_command_live

FAKE_COMMANDS = {
    "ok.py": 'print("hello from the fake command")',
    "fail.py": 'import sys\nprint("something went wrong")\nsys.exit(1)',
    "no_files.py": 'print("No files to upload! Please make sure the built extension versions match.")',
    "login_ok.py": 'print("Logging in to MyConfigura using e-mail: t@example.com")\nprint("Successfully logged in to MyConfigura.")',
    "login_fail.py": 'print("Logging in to MyConfigura using e-mail: t@example.com")\nprint("Failed to log in to MyConfigura.")',
    "make_fail.py": (
        'print("cop make (using cop version 16.5.2621.0)")\n'
        'print(" 1) custom.hbf  C:\\\\BuildLogs\\\\custom.hbf.buildLog.cmtxt")\n'
        'print(" * Errors     custom.hbf     (worker1, time: 00:01:42)")\n'
        'print("===== Work completed in 00:02:16: 1 item(s), 0 succeeded, 0 with warnings, 1 failed, 0 skipped or cancelled =====")'
    ),
    "make_warn.py": (
        'print(" 1) custom.hbf  C:\\\\BuildLogs\\\\custom.hbf.buildLog.cmtxt")\n'
        'print(" * Warning    custom.hbf     (worker1, time: 00:01:04)")\n'
        'print("===== Work completed in 00:01:28: 1 item(s), 0 succeeded, 1 with warnings, 0 failed, 0 skipped or cancelled =====")'
    ),
    "progress.py": (
        'import sys\n'
        'for p in (0, 50, 100):\n'
        '    sys.stdout.write(f"Receiving objects: {p:3}% ({p}/100)\\r")\n'
        'sys.stdout.write("\\nUpdating 1234..5678\\n")'
    ),
    "question.py": (
        'import sys, time\n'
        'print("Logging in to MyConfigura...", flush=True)\n'
        'sys.stdout.write("Password: ")\n'
        'sys.stdout.flush()\n'
        'time.sleep(2.5)\n'
        'print("\\nSuccessfully logged in to MyConfigura.")'
    ),
    "slow_marker.py": 'import sys, time\ntime.sleep(5)\nopen(sys.argv[1], "w").write("still ran")',
    "helper_keeps_pipe.py": (
        'import subprocess, sys\n'
        'helper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], stdout=sys.stdout)\n'
        'open(sys.argv[1], "w").write(str(helper.pid))\n'
        'print("done")'
    ),
}

class CommandRunnerTests(QuietTestCase):

    @classmethod
    def setUpClass(cls):
        cls.scripts = tempfile.mkdtemp(prefix="hni_build_fakes_")
        for name, code in FAKE_COMMANDS.items():
            write_file(os.path.join(cls.scripts, name), code + "\n")

    @classmethod
    def tearDownClass(cls):
        remove_folder(cls.scripts)

    def run_fake(self, script: str, *args: str, title: str = "FAKE", required_text: str = "") -> bool:
        command = [sys.executable, os.path.join(self.scripts, script), *args]
        return run_command_live(command, self.scripts, title, "the detail", required_text)

    # ---------------- results

    def test_success_and_log(self):
        self.assertTrue(self.run_fake("ok.py"))
        self.assertIn("[ OK ]", self.screen_text())
        self.assertIn("the detail", self.screen_text())
        self.assertIn("hello from the fake command", self.log_text())

    def test_exit_code_failure(self):
        self.assertFalse(self.run_fake("fail.py"))
        self.assertIn("[FAIL]", self.screen_text())
        self.assertIn("exit code 1", self.screen_text())
        self.assertIn("something went wrong", self.screen_text())

    def test_failure_message_with_exit_code_zero(self):
        self.assertFalse(self.run_fake("no_files.py"))
        self.assertIn("No files to upload", self.screen_text())

    def test_required_text_present(self):
        self.assertTrue(self.run_fake("login_ok.py", required_text="Successfully logged in to MyConfigura"))

    def test_required_text_missing(self):
        self.assertFalse(self.run_fake("ok.py", required_text="Successfully logged in to MyConfigura"))
        self.assertIn('did not get "Successfully logged in to MyConfigura"', self.screen_text())

    def test_login_failure_message_wins(self):
        self.assertFalse(self.run_fake("login_fail.py", required_text="Successfully logged in to MyConfigura"))
        self.assertIn("Failed to log in to MyConfigura", self.screen_text())

    # ---------------- cop make output

    def test_cop_make_failed_target(self):
        self.assertFalse(self.run_fake("make_fail.py", title="COP MAKE"))
        screen = self.screen_text()
        self.assertIn("1 failed", screen)
        self.assertIn("custom.hbf", screen)
        self.assertIn("custom.hbf.buildLog.cmtxt", screen)

    def test_cop_make_warnings_still_succeed_and_show_counts(self):
        self.assertTrue(self.run_fake("make_warn.py", title="COP MAKE"))
        screen = self.screen_text()
        self.assertIn("1 item(s), 0 succeeded, 1 with warnings, 0 failed", screen)
        self.assertIn("Warning", screen)

    def test_progress_lines_with_carriage_returns(self):
        self.assertTrue(self.run_fake("progress.py"))
        log = self.log_text()
        for percent in ("  0%", " 50%", "100%"):
            self.assertIn(f"Receiving objects: {percent}", log)
        self.assertIn("Updating 1234..5678", log)

    # ---------------- questions, missing programs, Ctrl+C, helpers

    def test_waiting_question_is_shown(self):
        self.assertTrue(self.run_fake("question.py"))
        self.assertIn("is waiting for an answer", self.screen_text())
        self.assertIn("Password:  <- waiting for an answer", self.log_text())

    def test_missing_program(self):
        self.assertFalse(run_command_live(["this-program-does-not-exist-123"], self.scripts, "MISSING"))
        self.assertIn("could not start", self.screen_text())

    def test_ctrl_c_stops_the_command_too(self):
        marker = os.path.join(self.scripts, "marker.txt")
        timer = threading.Timer(1.5, _thread.interrupt_main)
        self.addCleanup(timer.cancel)
        timer.start()

        with self.assertRaises(KeyboardInterrupt):
            self.run_fake("slow_marker.py", marker)

        # The fake would write the marker after 5 seconds if it was still running
        time.sleep(5)
        self.assertFalse(os.path.exists(marker), "the command kept running after Ctrl+C")
        self.assertIn("stopped with Ctrl+C", self.screen_text())

    def test_does_not_wait_for_helper_processes(self):
        # cop make starts build workers that keep the output open after cop has finished
        pid_file = os.path.join(self.scripts, "helper.pid")
        start = time.monotonic()
        self.assertTrue(self.run_fake("helper_keeps_pipe.py", pid_file))
        self.assertLess(time.monotonic() - start, 10)

        with open(pid_file) as file:
            helper_pid = int(file.read())
        try:
            os.kill(helper_pid, signal.SIGTERM)
        except OSError:
            pass

if __name__ == "__main__":
    unittest.main()
