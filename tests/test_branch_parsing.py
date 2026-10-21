# ============================================================
# Project      : HNI Build Automation
# File         : test_branch_parsing.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Tests for reading branch names: the version in a branch name,
# the "Latest" release branch, and checking typed branch names.
# No Git needed.
#
# ============================================================

import unittest

import tests.helpers

from pipeline.git_operations import (
    get_version_string_from_branch,
    is_numeric_version,
    get_latest_release_branch,
    validate_release_branch,
    validate_test_branch,
    get_test_version_string_from_branch
)

RELEASE_BRANCHES = ["  origin/release/17.0.9", "  origin/release/17.5.0", "  origin/release/16.5.9"]
TEST_BRANCHES = ["  origin/test/Demo.Build.17.5.0"]

class VersionFromBranchTests(unittest.TestCase):

    def test_release_branch_version_is_last_part(self):
        self.assertEqual(get_version_string_from_branch("  origin/release/16.5.9 "), "16.5.9")

    def test_test_branch_version_is_only_the_numbers(self):
        self.assertEqual(get_test_version_string_from_branch("origin/test/demo.build.17.5.0"), "17.5.0")

    def test_numeric_versions(self):
        self.assertTrue(is_numeric_version("17.5.0"))
        self.assertTrue(is_numeric_version("16"))

    def test_not_numeric_versions(self):
        for version in ["17.5.0-hotfix", "", "17..5", "demo", "17.5.x"]:
            with self.subTest(version=version):
                self.assertFalse(is_numeric_version(version))

class LatestReleaseBranchTests(unittest.TestCase):

    def test_picks_the_highest_version(self):
        self.assertEqual(get_latest_release_branch(RELEASE_BRANCHES), "origin/release/17.5.0")

    def test_compares_numbers_not_text(self):
        branches = ["origin/release/17.9.0", "origin/release/17.10.0"]
        self.assertEqual(get_latest_release_branch(branches), "origin/release/17.10.0")

    def test_skips_branches_that_are_not_plain_versions(self):
        branches = ["origin/release/17.5.0", "origin/release/17.6.0-hotfix", "origin/release/abc"]
        self.assertEqual(get_latest_release_branch(branches), "origin/release/17.5.0")

    def test_no_branches_gives_none(self):
        self.assertIsNone(get_latest_release_branch([]))

class ValidateReleaseBranchTests(unittest.TestCase):

    def test_accepts_the_three_ways_of_typing_it(self):
        for typed in ["origin/release/17.5.0", "release/17.5.0", "17.5.0", " Release/17.5.0 "]:
            with self.subTest(typed=typed):
                self.assertEqual(validate_release_branch(typed, RELEASE_BRANCHES), "origin/release/17.5.0")

    def test_unknown_branch_gives_none(self):
        self.assertIsNone(validate_release_branch("99.0.0", RELEASE_BRANCHES))

class ValidateTestBranchTests(unittest.TestCase):

    def test_accepts_the_three_ways_and_keeps_the_real_case(self):
        for typed in ["origin/test/demo.build.17.5.0", "test/demo.build.17.5.0", "demo.build.17.5.0"]:
            with self.subTest(typed=typed):
                self.assertEqual(validate_test_branch(typed, TEST_BRANCHES), "origin/test/Demo.Build.17.5.0")

    def test_release_branch_is_not_a_test_branch(self):
        self.assertIsNone(validate_test_branch("release/16.5.9", TEST_BRANCHES))

if __name__ == "__main__":
    unittest.main()
