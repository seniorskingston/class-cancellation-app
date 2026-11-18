"""Safety switches for production and the separate test environment.

The live site does not set APP_ENV, so it stays in production mode.
The test site sets APP_ENV=test. In that mode the app refuses to start
when it is pointed at the production database, and it does not send email
or run the scheduled reports.
"""

import os

PRODUCTION_SUPABASE_REF = "ptyqolpecpqebuzwwcsn"
FEATURE_NEW_FUNCTION = "NEW_FUNCTION"


def app_env() -> str:
    value = os.getenv("APP_ENV", "production").strip().lower()
    if value in ("test", "testing", "development"):
        return "test"
    return "production"


def is_test() -> bool:
    return app_env() == "test"


def _flag_on(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


def emails_enabled() -> bool:
    """Test mode never sends mail, even if EMAILS_ENABLED is set."""
    if is_test():
        return False
    return _flag_on("EMAILS_ENABLED", "true")


def scheduled_actions_enabled() -> bool:
    """Test mode does not start the daily or weekly email jobs."""
    if is_test():
        return False
    return _flag_on("SCHEDULED_ACTIONS_ENABLED", "true")


def feature_enabled(name: str) -> bool:
    """New functions stay off until FEATURE_<NAME> is set to true."""
    return _flag_on(f"FEATURE_{name}", "false")


def assert_test_database_is_separate() -> None:
    if not is_test():
        return
    url = os.getenv("SUPABASE_URL", "")
    if PRODUCTION_SUPABASE_REF in url:
        raise RuntimeError(
            "The test environment is pointed at the production database. "
            "Startup was stopped so production records cannot be changed. "
            "Create a separate Supabase project and put its address in the test site settings."
        )


def public_status() -> dict:
    return {
        "app_env": app_env(),
        "emails_enabled": emails_enabled(),
        "scheduled_actions_enabled": scheduled_actions_enabled(),
        "features": {
            "new_function": feature_enabled(FEATURE_NEW_FUNCTION),
        },
    }
