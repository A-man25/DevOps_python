# ============================================================
# Project      : HNI Build Automation
# File         : test_input_parsing.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Tests for turning answers into build types and extensions,
# the extension -> COP group map, and questions that ask again
# when the answer is wrong.
#
# ============================================================

import unittest

from tests.helpers import QuietTestCase

from models.enums import (
    Build_Type,
    Extension
)

from ui.input_handler import (
    get_build_type_enum,
    get_extension_enum,
    get_build_confirmation,
    get_retry_confirmation
)

from config.extension_config import (
    get_cop_extension_groups
)

class BuildTypeTests(unittest.TestCase):

    def test_numbers_and_names(self):
        self.assertEqual(get_build_type_enum("1"), Build_Type.BETA)
        self.assertEqual(get_build_type_enum(" BETA "), Build_Type.BETA)
        self.assertEqual(get_build_type_enum("2"), Build_Type.FIRST_AID)
        self.assertEqual(get_build_type_enum("project based"), Build_Type.PROJECT_BASED)

    def test_unknown_answer_is_none(self):
        self.assertEqual(get_build_type_enum("x"), Build_Type.NONE)

class ExtensionTests(unittest.TestCase):

    def test_numbers_and_names_mixed(self):
        self.assertEqual(get_extension_enum(["1", " hbf", "5 "]), [Extension.HON, Extension.HBF, Extension.HNI_CORE])

    def test_duplicates_are_removed(self):
        self.assertEqual(get_extension_enum(["4", "hbf", "4"]), [Extension.HBF])

    def test_unknown_extension_is_marked_none(self):
        self.assertIn(Extension.NONE, get_extension_enum(["1", "9"]))

    def test_every_extension_has_a_cop_group(self):
        extensions = [Extension.HON, Extension.ALLSTEEL, Extension.GUNLOCKE, Extension.HBF, Extension.HNI_CORE]
        self.assertEqual(get_cop_extension_groups(extensions), ["[hon]", "[asi]", "[gunlocke]", "[hbf]", "[hniCore]"])

class QuestionTests(QuietTestCase):

    def test_wrong_answer_asks_again(self):
        self.answer("maybe", "y")
        self.assertTrue(get_build_confirmation())
        self.assertIn("Incorrect input.", self.screen_text())

    def test_no_is_false(self):
        self.answer("n")
        self.assertFalse(get_retry_confirmation("Git push"))

if __name__ == "__main__":
    unittest.main()
