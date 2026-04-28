# NestClaw Local LLM Provider Onboarding Guide

## Purpose
This guide defines the first real local LLM onboarding path for Stage 12. The target is not a free-form agent. The target is a local provider that can run only approved NestClaw job templates through profile, capability pack, budget, sensitivity, and audit boundaries.

## Baseline Provider
The first promoted local provider is Ollama:

- model registry provider: `local_primary`
- provider type: `local`
- engine: `ollama`
- default model: `llama3.1:8b`
- production profile: `local_ollama_ops`
- provider class: `local_llm`

`local_ollama_ops` is allowed to run:

- `daily_status_digest`
- `issue_triage`
- `readiness_check`

It is not allowed to send payloads externally. It uses the same curated capability packs as the default local operations profile.

## Onboarding Sequence
1. Install or start Ollama on the local machine.
2. Pull the configured model, for example `ollama pull llama3.1:8b`.
3. Confirm `configs/model_registry.yaml` contains `local_primary` with `engine: ollama`.
4. Confirm `configs/agent_profiles.json` contains `local_ollama_ops`.
5. Run the strict harness validator.
6. Run the local LLM onboarding smoke.
7. Use `newclaw job run` only through approved job templates.

## Required Checks
```bash
python3 scripts/validate_stage12_llm_harness.py --strict-warnings
env PATH=../nestclaw-ideation-qa/.venv/bin:$PATH \
  bash scripts/run_stage12_local_llm_onboarding_smoke.sh
```

Optional live Ollama check:

```bash
env PATH=../nestclaw-ideation-qa/.venv/bin:$PATH \
  NEWCLAW_STAGE12_OLLAMA_LIVE_CHECK=1 \
  bash scripts/run_stage12_local_llm_onboarding_smoke.sh
```

The default smoke proves NestClaw can resolve the local Ollama profile and execute a bounded job through the existing runtime. The optional live check additionally verifies that the local `ollama` command is present and can list models.

## Operator Rule
Do not give local LLMs direct access to the full tool registry. Add or change capability packs first, run the validator, and then run the Stage 12 QA cycle.
