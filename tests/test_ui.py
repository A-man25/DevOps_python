# ============================================================
# Project      : HNI Build Automation
# File         : test_ui.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Tests for the screen code: ui/progress.py, ui/display.py and
# ui/colours.py.
#
# ============================================================

import os
import unittest
from unittest import mock

from tests.helpers import QuietTestCase, ANSI_CODE_PATTERN

from models.enums import (
    Build_Type,
    Extension
)

import ui.progress as progress

from ui.display import (
    prompt_text,
    show_build_summary,
    show_changed_files,
    show_check,
    show_build_stopped
)

from ui.colours import (
    enable_console_colours
)

class ProgressPieceTests(unittest.TestCase):

    def test_elapsed_time(self):
        self.assertEqual(progress.format_elapsed_time(0), "00:00:00")
        self.assertEqual(progress.format_elapsed_time(3725.9), "01:02:05")

    def test_bar_fills_with_the_percent(self):
        self.assertEqual(progress.get_progress_bar(0, 0), "░" * progress.BAR_WIDTH)
        self.assertEqual(progress.get_progress_bar(100, 0), "█" * progress.BAR_WIDTH)
        self.assertEqual(progress.get_progress_bar(50, 0).count("█"), progress.BAR_WIDTH // 2)

    def test_unknown_percent_bounces_and_keeps_its_width(self):
        for frame in range(60):
            bar = progress.get_progress_bar(None, frame)
            self.assertEqual(len(bar), progress.BAR_WIDTH)
            self.assertEqual(bar.count("█"), progress.BOUNCE_BLOCK_WIDTH)

class ProgressLineTests(QuietTestCase):

    def test_line_never_wider_than_the_window(self):
        with mock.patch.object(progress.shutil, "get_terminal_size", return_value=os.terminal_size((60, 20))):
            progress.show_progress("COP MAKE", 125, 42, "a very long status text " * 10, 3)
        line = ANSI_CODE_PATTERN.sub("", self.screen.getvalue()).replace("\r", "")
        self.assertLessEqual(len(line), 59)
        self.assertIn("42%", line)

    def test_normal_window_shows_the_bar(self):
        with mock.patch.object(progress.shutil, "get_terminal_size", return_value=os.terminal_size((120, 30))):
            progress.show_progress("COP MAKE", 125, 50, "custom.hbf", 3)
        line = ANSI_CODE_PATTERN.sub("", self.screen.getvalue()).replace("\r", "")
        self.assertLessEqual(len(line), 119)
        self.assertIn("█" * (progress.BAR_WIDTH // 2), line)
        self.assertIn("custom.hbf", line)

    def test_result_lines(self):
        progress.show_result("GIT PUSH", 5, True, "done")
        progress.show_result("COP MAKE", 5, False, "1 failed")
        screen = self.screen_text()
        self.assertIn("[ OK ]  GIT PUSH", screen)
        self.assertIn("[FAIL]  COP MAKE", screen)

    def test_failure_details(self):
        progress.show_failure_details(["custom.hbf"], {"custom.hbf": "C:\\logs\\hbf.cmtxt"},
                                      ["last line"], "C:\\cop.log", "C:\\build.log", "a hint")
        screen = self.screen_text()
        for text in ["a hint", "custom.hbf", "C:\\logs\\hbf.cmtxt", "last line", "C:\\cop.log", "C:\\build.log"]:
            self.assertIn(text, screen)

    def test_compile_errors_are_capped(self):
        progress.show_compile_errors([f"error {n}" for n in range(50)], max_lines=10)
        screen = self.screen_text()
        self.assertIn("error 9", screen)
        self.assertNotIn("error 10", screen)
        self.assertIn("40 more line(s)", screen)

class DisplayTests(QuietTestCase):

    def test_summary_shows_every_value(self):
        show_build_summary(Build_Type.BETA, [Extension.HON, Extension.HBF], "origin/release/17.5.0",
                           "17.5.0", "17.5.0.26", "17.5.0.27")
        screen = self.screen_text()
        for text in ["BETA", "HON, HBF", "origin/release/17.5.0", "17.5.0.26", "17.5.0.27"]:
            self.assertIn(text, screen)

    def test_changed_files_new_files_are_not_counted(self):
        show_changed_files([" M hbf/extension.xml", "?? hbf/_automaticSecurityDelegates.cm"])
        screen = self.screen_text()
        self.assertIn("1 file(s) will be committed", screen)
        self.assertIn("will NOT be committed", screen)

    def test_check_lines(self):
        show_check("Git installed", True, "C:\\git.exe")
        show_check("COP installed", False, "cop was not found")
        screen = self.screen_text()
        self.assertIn("[ OK ]  Git installed", screen)
        self.assertIn("[FAIL]  COP installed", screen)

    def test_stopped_box_shows_the_reason(self):
        show_build_stopped("Failed during COP make.")
        self.assertIn("BETA BUILD STOPPED", self.screen_text())
        self.assertIn("Failed during COP make.", self.screen_text())

    def test_prompt_text(self):
        self.assertIn("Proceed? [y/n]: ", ANSI_CODE_PATTERN.sub("", prompt_text("Proceed? [y/n]: ")))

    def test_colours_can_be_turned_on(self):
        enable_console_colours()

if __name__ == "__main__":
    unittest.main()
