from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

MODULE_PATH = Path("app/services/planner_executor_service.py")
MODULE_SPEC = spec_from_file_location("planner_executor_service", MODULE_PATH)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
MODULE = module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(MODULE)

build_action_result = MODULE.build_action_result
emit_planning_events = MODULE.emit_planning_events
execute_planned_actions = MODULE.execute_planned_actions
record_action_results = MODULE.record_action_results
record_planning_snapshot = MODULE.record_planning_snapshot


class TestPlannerExecutorService(unittest.TestCase):
    def test_build_action_result_preserves_common_fields(self) -> None:
        result = build_action_result(
            {"action_id": "act_1", "tool_id": "redmine.issue.create"},
            status="dry-run",
            adapter="redmine_mcp",
            method="issue.create",
            mode="dry-run",
            request_payload={"subject": "ops"},
            extra={"external_ref": "RM-1"},
        )
        self.assertEqual(
            result,
            {
                "action_id": "act_1",
                "status": "dry-run",
                "tool_id": "redmine.issue.create",
                "adapter": "redmine_mcp",
                "method": "issue.create",
                "mode": "dry-run",
                "request_payload": {"subject": "ops"},
                "external_ref": "RM-1",
            },
        )

    def test_record_planning_snapshot_and_action_results_persist_common_contract(self) -> None:
        persisted: list[dict[str, object]] = []
        task: dict[str, object] = {"task_id": "task-1"}
        planned_actions = [{"action_id": "act_1", "tool_id": "internal.summary.generate"}]
        planning_provenance = {"source": "llm", "confidence": 0.9}
        action_results = [
            {
                "action_id": "act_1",
                "tool_id": "internal.summary.generate",
                "adapter": "provider_invoker",
                "method": "summary.generate",
                "mode": "renderer",
                "request_payload": {"notes": "hello"},
                "output_text": "summary",
            }
        ]

        record_planning_snapshot(
            task,
            planned_actions=planned_actions,
            planning_provenance=planning_provenance,
            now_iso=lambda: "2026-04-04T00:00:00+00:00",
            persist_task=lambda item: persisted.append(dict(item)),
        )
        record_action_results(
            task,
            action_results=action_results,
            now_iso=lambda: "2026-04-04T00:00:01+00:00",
            persist_task=lambda item: persisted.append(dict(item)),
            serializer=lambda item: {key: value for key, value in item.items() if key != "output_text"},
        )

        self.assertEqual(task["planned_actions"], planned_actions)
        self.assertEqual(task["planning_provenance"], planning_provenance)
        self.assertEqual(task["action_results"][0]["tool_id"], "internal.summary.generate")
        self.assertNotIn("output_text", task["action_results"][0])
        self.assertEqual(len(persisted), 2)

    def test_execute_planned_actions_reuses_prior_results_binding_chain(self) -> None:
        captured: list[tuple[str, list[str]]] = []

        def fake_dispatch(task: dict[str, object], planned_action: dict[str, object], *, prior_results: list[dict[str, object]], **_: object) -> dict[str, object]:
            captured.append((str(planned_action["action_id"]), [str(item["action_id"]) for item in prior_results]))
            return {
                "action_id": planned_action["action_id"],
                "tool_id": planned_action["tool_id"],
                "adapter": "fake",
                "method": "run",
                "mode": "dry-run",
                "request_payload": {"task_id": task["task_id"]},
                "status": "dry-run",
            }

        results = execute_planned_actions(
            {"task_id": "task-1"},
            [
                {"action_id": "act_1", "tool_id": "tool.one"},
                {"action_id": "act_2", "tool_id": "tool.two"},
            ],
            dispatch_action=fake_dispatch,
        )

        self.assertEqual(captured, [("act_1", []), ("act_2", ["act_1"])])
        self.assertEqual([item["action_id"] for item in results], ["act_1", "act_2"])

    def test_emit_planning_events_supports_fallback_and_count(self) -> None:
        events: list[tuple[str, dict[str, object]]] = []

        def fake_log_event(task_id: str, event_type: str, **payload: object) -> None:
            events.append((event_type, {"task_id": task_id, **payload}))

        emit_planning_events(
            "task-1",
            planning_provenance={
                "source": "heuristic_fallback",
                "confidence": 0.3,
                "degraded_mode": True,
                "fallback_reason": "llm_disabled",
                "provider_selection": {"provider_id": "local", "provider_type": "openai-compatible"},
            },
            planned_actions=[{"tool_id": "internal.summary.generate"}, {"tool_id": "redmine.issue.create"}],
            log_event=fake_log_event,
            plan_generated_event="TASK_PLAN_GENERATED",
            actions_planned_event="TASK_ACTIONS_PLANNED",
            fallback_event="TASK_PLAN_FALLBACK",
        )

        self.assertEqual([item[0] for item in events], ["TASK_PLAN_FALLBACK", "TASK_PLAN_GENERATED", "TASK_ACTIONS_PLANNED", "PLANNED_ACTIONS_BUILT"])
        self.assertEqual(events[1][1]["action_count"], 2)


if __name__ == "__main__":
    unittest.main()
