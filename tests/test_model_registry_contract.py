from __future__ import annotations

import unittest

from app.model_registry import load_model_registry, select_provider


class TestModelRegistryContract(unittest.TestCase):
    def test_load_model_registry_from_yaml(self) -> None:
        registry = load_model_registry()

        self.assertEqual(registry.version, 1)
        self.assertEqual(len(registry.providers), 3)
        self.assertEqual(len(registry.routing_rules), 4)

    def test_selects_api_provider_for_low_summarize(self) -> None:
        registry = load_model_registry()

        selection = select_provider(registry, sensitivity="low", task_type="summarize", external_send=False)

        self.assertEqual(selection.provider_id, "api_general")
        self.assertEqual(selection.selection_source, "routing_rule")
        self.assertFalse(selection.requires_human_approval)

    def test_selects_local_provider_for_intent_classification(self) -> None:
        registry = load_model_registry()

        selection = select_provider(registry, sensitivity="low", task_type="classify_intent", external_send=False)

        self.assertEqual(selection.provider_id, "local_lmstudio")
        self.assertEqual(selection.engine, "lmstudio")
        self.assertEqual(selection.selection_source, "routing_rule")

    def test_selects_local_provider_for_high_sensitivity(self) -> None:
        registry = load_model_registry()

        selection = select_provider(registry, sensitivity="high", task_type="summarize", external_send=False)

        self.assertEqual(selection.provider_id, "local_primary")
        self.assertEqual(selection.engine, "ollama")

    def test_external_send_sets_human_approval_flag(self) -> None:
        registry = load_model_registry()

        selection = select_provider(registry, sensitivity="low", task_type="summarize", external_send=True)

        self.assertEqual(selection.provider_id, "api_general")
        self.assertTrue(selection.requires_human_approval)

    def test_unmatched_context_falls_back_to_first_enabled_provider(self) -> None:
        registry = load_model_registry()

        selection = select_provider(registry, sensitivity="low", task_type="incident_response", external_send=False)

        self.assertEqual(selection.provider_id, "local_primary")
        self.assertEqual(selection.selection_source, "default_enabled_provider")


if __name__ == "__main__":
    unittest.main()
