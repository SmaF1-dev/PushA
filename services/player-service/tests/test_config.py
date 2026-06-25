import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from app.config import AppEnvironment, get_settings, load_settings


class SettingsTests(unittest.TestCase):
    def tearDown(self) -> None:
        get_settings.cache_clear()

    def test_loads_local_env_file(self) -> None:
        settings = load_settings()

        self.assertIs(settings.app_env, AppEnvironment.DEVELOPMENT)
        self.assertEqual(settings.http_port, 8000)
        self.assertEqual(settings.grpc_port, 50051)
        self.assertTrue(settings.postgres_user)
        self.assertEqual(
            settings.database_url.hosts()[0]["host"], settings.postgres_host
        )
        self.assertEqual(settings.database_url.path, f"/{settings.postgres_db}")

    def test_process_environment_overrides_env_file(self) -> None:
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "DEBUG": "false",
                "HTTP_PORT": "9000",
                "POSTGRES_USER": "production-player",
                "POSTGRES_PASSWORD": "secret",
                "POSTGRES_HOST": "production-db",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "production-player-db",
                "POSTGRES_SQL_ECHO": "true",
            },
        ):
            settings = load_settings()

        self.assertIs(settings.app_env, AppEnvironment.PRODUCTION)
        self.assertFalse(settings.debug)
        self.assertEqual(settings.http_port, 9000)
        self.assertEqual(settings.postgres_user, "production-player")
        self.assertEqual(settings.database_url.hosts()[0]["host"], "production-db")
        self.assertEqual(settings.database_url.path, "/production-player-db")
        self.assertTrue(settings.postgres_sql_echo)

    def test_rejects_invalid_postgres_port(self) -> None:
        with patch.dict(os.environ, {"POSTGRES_PORT": "70000"}):
            with self.assertRaises(ValidationError):
                load_settings()

    def test_get_settings_returns_cached_instance(self) -> None:
        self.assertIs(get_settings(), get_settings())


if __name__ == "__main__":
    unittest.main()
