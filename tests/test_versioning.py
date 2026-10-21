# ============================================================
# Project      : HNI Build Automation
# File         : test_versioning.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Tests for pipeline/versioning.py: picking the next build
# number from the Git tags, and the upload name.
#
# ============================================================

import unittest

import tests.helpers

from pipeline.versioning import (
    get_release_build_tags,
    get_latest_build_number,
    get_next_build_version,
    get_beta_upload_name
)

class ReleaseBuildTagTests(unittest.TestCase):

    def test_keeps_only_tags_of_this_release(self):
        tags = ["16.5.9.8", "16.5.9.9", "17.0.9.25", "16.5.10.1"]
        self.assertEqual(get_release_build_tags(tags, "16.5.9"), ["16.5.9.8", "16.5.9.9"])

    def test_ignores_tags_that_are_not_plain_build_numbers(self):
        tags = ["17.5.0.2", "17.5.0.21-test", "17.5.0.x", "17.5.0.", "17.5.0.3.1", "17.5.01"]
        self.assertEqual(get_release_build_tags(tags, "17.5.0"), ["17.5.0.2"])

    def test_spaces_around_tags_are_ignored(self):
        self.assertEqual(get_release_build_tags(["  17.5.0.11  "], "17.5.0"), ["17.5.0.11"])

class NextBuildVersionTests(unittest.TestCase):

    def test_next_build_is_highest_plus_one(self):
        tags = ["16.5.9.8", "16.5.9.9", "16.5.9.10"]
        latest = get_latest_build_number(get_release_build_tags(tags, "16.5.9"))
        self.assertEqual(get_next_build_version("16.5.9", latest), "16.5.9.11")

    def test_numbers_are_compared_as_numbers_not_text(self):
        # As text "9" > "10"; as numbers 10 > 9
        self.assertEqual(get_latest_build_number(["17.5.0.9", "17.5.0.10"]), 10)

    def test_first_build_of_a_release_is_1(self):
        latest = get_latest_build_number(get_release_build_tags(["17.0.9.25"], "17.5.0"))
        self.assertEqual(get_next_build_version("17.5.0", latest), "17.5.0.1")

    def test_odd_tags_do_not_crash(self):
        tags = ["17.5.0.21-test", "17.5.0.x", "17.5.0.4"]
        self.assertEqual(get_latest_build_number(get_release_build_tags(tags, "17.5.0")), 4)

class UploadNameTests(unittest.TestCase):

    def test_dots_become_dashes_and_beta_is_added(self):
        self.assertEqual(get_beta_upload_name("16.5.9.11"), "16-5-9-11@BETA")

if __name__ == "__main__":
    unittest.main()
