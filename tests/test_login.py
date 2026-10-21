# ============================================================
# Project      : HNI Build Automation
# File         : test_login.py
# Author       : Aman Rajesh Choudhari
# Created      : 21-Oct-2026
#
# Description:
# Tests for the MyConfigura login:
# - where the login comes from (Windows, saved, typed)
# - saving, using and removing the saved login
# - cop login only counts when COP says it worked
# - the real Windows Credential Manager (under a test name)
#
# ============================================================

import os
import sys
import tempfile
import unittest
from unittest import mock

from tests.helpers import QuietTestCase, IS_WINDOWS, remove_folder, write_file

import workflow.beta_build_flow as flow
import pipeline.cop_operations as cop_operations

LOGIN_ENV = ["CETDEV_MC_USERNAME", "CETDEV_MC_PASSWORD"]

class LoginTestCase(QuietTestCase):
    """Runs every test with the login environment variables cleared and restored afterwards."""

    def setUp(self):
        super().setUp()
        env_patch = mock.patch.dict(os.environ)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        for name in LOGIN_ENV:
            os.environ.pop(name, None)

class LoginFlowTests(LoginTestCase):

    def setUp(self):
        super().setUp()
        self.saved = {}
        self.typed_count = 0
        self.login_results = []
        fakes = {
            "load_saved_login": lambda: self.saved.get("login"),
            "save_login": self.fake_save,
            "delete_saved_login": lambda: self.saved.pop("login", None),
            "get_myconfigura_login": self.fake_typed_login,
            "cop_login": lambda repo: self.login_results.pop(0),
        }
        for name, fake in fakes.items():
            patcher = mock.patch.object(flow, name, fake)
            patcher.start()
            self.addCleanup(patcher.stop)

    def fake_save(self, email, password):
        self.saved["login"] = (email, password)
        return True

    def fake_typed_login(self):
        self.typed_count += 1
        return ("tester@example.com", f"secret-{self.typed_count}")

    def test_typed_login_is_saved_when_you_say_yes(self):
        self.login_results = [True]
        self.answer("y")
        self.assertTrue(flow.login_to_myconfigura("."))
        self.assertEqual(self.saved["login"], ("tester@example.com", "secret-1"))

    def test_typed_login_is_not_saved_when_you_say_no(self):
        self.login_results = [True]
        self.answer("n")
        self.assertTrue(flow.login_to_myconfigura("."))
        self.assertNotIn("login", self.saved)

    def test_saved_login_is_used_without_questions(self):
        self.saved["login"] = ("tester@example.com", "saved-secret")
        self.login_results = [True]
        self.assertTrue(flow.login_to_myconfigura("."))
        self.assertEqual(self.typed_count, 0)
        self.assertEqual(os.environ["CETDEV_MC_PASSWORD"], "saved-secret")

    def test_saved_login_that_fails_is_removed(self):
        self.saved["login"] = ("tester@example.com", "old-password")
        self.login_results = [False]
        self.answer("n")
        self.assertFalse(flow.login_to_myconfigura("."))
        self.assertNotIn("login", self.saved)
        self.assertNotIn("CETDEV_MC_PASSWORD", os.environ)

    def test_wrong_then_right_login(self):
        self.login_results = [False, True]
        self.answer("y", "n")
        self.assertTrue(flow.login_to_myconfigura("."))
        self.assertEqual(self.typed_count, 2)
        self.assertEqual(os.environ["CETDEV_MC_PASSWORD"], "secret-2")

    def test_login_already_set_in_windows_is_not_asked(self):
        os.environ["CETDEV_MC_USERNAME"] = "windows@example.com"
        os.environ["CETDEV_MC_PASSWORD"] = "from-windows"
        self.login_results = [True]
        self.assertTrue(flow.login_to_myconfigura("."))
        self.assertEqual(self.typed_count, 0)
        self.assertNotIn("login", self.saved)

class CopLoginTests(LoginTestCase):
    """cop login exits with code 0 even when it fails: only COP's success message counts."""

    def setUp(self):
        super().setUp()
        self.scripts = tempfile.mkdtemp(prefix="hni_build_fakes_")
        self.addCleanup(remove_folder, self.scripts)

    def run_cop_login_with_fake(self, fake_code: str) -> bool:
        script = os.path.join(self.scripts, "fake_cop_login.py")
        write_file(script, fake_code)
        real_run = cop_operations.run_command_live
        def run_fake_instead(command, cwd, title, detail="", required_text=""):
            return real_run([sys.executable, script], self.scripts, title, detail, required_text)

        with mock.patch.object(cop_operations, "run_command_live", run_fake_instead):
            return cop_operations.cop_login(self.scripts)

    def test_login_failure_with_exit_code_zero_is_a_failure(self):
        cop_operations.set_cop_login("wrong@example.com", "bad")
        self.assertFalse(self.run_cop_login_with_fake('print("Failed to log in to MyConfigura.")\n'))

    def test_login_success(self):
        cop_operations.set_cop_login("tester@example.com", "good")
        self.assertTrue(self.run_cop_login_with_fake('print("Successfully logged in to MyConfigura.")\n'))
        self.assertIn("tester@example.com", self.screen_text())

    def test_password_is_never_shown_or_logged(self):
        cop_operations.set_cop_login("tester@example.com", "TopSecret123")
        self.run_cop_login_with_fake('print("Successfully logged in to MyConfigura.")\n')
        self.assertNotIn("TopSecret123", self.screen_text())
        self.assertNotIn("TopSecret123", self.log_text())

    def test_set_and_clear(self):
        cop_operations.set_cop_login("a@example.com", "b")
        self.assertTrue(cop_operations.is_cop_login_set())
        cop_operations.clear_cop_login()
        self.assertFalse(cop_operations.is_cop_login_set())

@unittest.skipUnless(IS_WINDOWS, "Windows Credential Manager only exists on Windows")
class CredentialStoreTests(unittest.TestCase):
    """Uses the real Windows Credential Manager, under a test name (never the real login)."""

    def setUp(self):
        import utils.credential_store as credential_store
        self.store = credential_store
        name_patch = mock.patch.object(credential_store, "CREDENTIAL_NAME", "HNI_Build_Automation/TEST_SUITE")
        name_patch.start()
        self.addCleanup(name_patch.stop)
        self.addCleanup(credential_store.delete_saved_login)
        credential_store.delete_saved_login()

    def test_nothing_saved(self):
        self.assertIsNone(self.store.load_saved_login())

    def test_save_load_delete(self):
        password = "pä$$ wörd!#1 ✓"
        self.assertTrue(self.store.save_login("tester@example.com", password))
        self.assertEqual(self.store.load_saved_login(), ("tester@example.com", password))
        self.store.delete_saved_login()
        self.assertIsNone(self.store.load_saved_login())

    def test_save_replaces_the_old_login(self):
        self.store.save_login("old@example.com", "old")
        self.store.save_login("new@example.com", "new")
        self.assertEqual(self.store.load_saved_login(), ("new@example.com", "new"))

if __name__ == "__main__":
    unittest.main()
