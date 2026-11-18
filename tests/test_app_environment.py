"""Checks for the test-environment safety switches. These do not touch a database."""

import os
import unittest

import app_environment


class TestAppEnvironment(unittest.TestCase):
    def setUp(self):
        self.keys = (
            "APP_ENV",
            "EMAILS_ENABLED",
            "SCHEDULED_ACTIONS_ENABLED",
            "FEATURE_NEW_FUNCTION",
            "SUPABASE_URL",
        )
        self.saved = {key: os.environ.get(key) for key in self.keys}
        for key in self.keys:
            os.environ.pop(key, None)

    def tearDown(self):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_production_defaults_keep_current_behavior(self):
        self.assertEqual(app_environment.app_env(), "production")
        self.assertTrue(app_environment.emails_enabled())
        self.assertTrue(app_environment.scheduled_actions_enabled())
        self.assertFalse(app_environment.feature_enabled("NEW_FUNCTION"))

    def test_test_mode_blocks_email_and_scheduled_jobs(self):
        os.environ["APP_ENV"] = "test"
        os.environ["EMAILS_ENABLED"] = "true"
        os.environ["SCHEDULED_ACTIONS_ENABLED"] = "true"
        self.assertFalse(app_environment.emails_enabled())
        self.assertFalse(app_environment.scheduled_actions_enabled())

    def test_test_mode_refuses_the_production_database(self):
        os.environ["APP_ENV"] = "test"
        os.environ["SUPABASE_URL"] = "https://ptyqolpecpqebuzwwcsn.supabase.co"
        with self.assertRaises(RuntimeError):
            app_environment.assert_test_database_is_separate()

    def test_test_mode_allows_a_different_database(self):
        os.environ["APP_ENV"] = "test"
        os.environ["SUPABASE_URL"] = "https://test-project.supabase.co"
        app_environment.assert_test_database_is_separate()

    def test_production_mode_can_use_the_production_database(self):
        os.environ["SUPABASE_URL"] = "https://ptyqolpecpqebuzwwcsn.supabase.co"
        app_environment.assert_test_database_is_separate()

    def test_feature_flag_is_off_until_requested(self):
        self.assertFalse(app_environment.feature_enabled(app_environment.FEATURE_NEW_FUNCTION))
        os.environ["FEATURE_NEW_FUNCTION"] = "true"
        self.assertTrue(app_environment.feature_enabled(app_environment.FEATURE_NEW_FUNCTION))


if __name__ == "__main__":
    unittest.main()
