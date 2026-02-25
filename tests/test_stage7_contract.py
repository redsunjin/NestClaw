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

    def test_browser_smoke_script_exists_and_executable(self) -> None:
        script = Path("scripts/run_browser_smoke.sh")
        self.assertTrue(script.is_file())
        self.assertNotEqual(script.stat().st_mode & 0o111, 0)

    def test_postgres_rehearsal_script_exists_and_executable(self) -> None:
        script = Path("scripts/run_postgres_rehearsal.sh")
        self.assertTrue(script.is_file())
        self.assertNotEqual(script.stat().st_mode & 0o111, 0)

    def test_cycle_script_integrates_browser_smoke(self) -> None:
        source = Path("scripts/run_dev_qa_cycle.sh").read_text(encoding="utf-8")
        self.assertIn("run_optional_dep_check", source)
        self.assertIn("browser swagger smoke (playwright)", source)
        self.assertIn("scripts/run_browser_smoke.sh", source)
        self.assertIn("[[ \"$rc\" -eq 10 ]]", source)

    def test_cycle_script_integrates_postgres_rehearsal(self) -> None:
        source = Path("scripts/run_dev_qa_cycle.sh").read_text(encoding="utf-8")
        self.assertIn("postgres rehearsal smoke (env-gated)", source)
        self.assertIn("scripts/run_postgres_rehearsal.sh", source)


if __name__ == "__main__":
    unittest.main()
