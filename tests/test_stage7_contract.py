import unittest
from pathlib import Path


class TestStage7Contract(unittest.TestCase):
    def test_postgres_store_exists(self) -> None:
        source = Path("app/persistence.py").read_text(encoding="utf-8")
        self.assertIn("class PostgresStateStore", source)
        self.assertIn("def create_state_store", source)

    def test_migration_assets_exist(self) -> None:
        self.assertTrue(Path("migrations/postgres/001_init.sql").is_file())
        self.assertTrue(Path("migrations/postgres/001_down.sql").is_file())
        self.assertTrue(Path("scripts/migrate_postgres.sh").is_file())

    def test_idp_verification_hooks_exist(self) -> None:
        source = Path("app/auth.py").read_text(encoding="utf-8")
        self.assertIn("NEWCLAW_IDP_JWKS_PATH", source)
        self.assertIn("X-SSO-Token", source)
        self.assertIn("_decode_idp_jwt", source)


if __name__ == "__main__":
    unittest.main()
