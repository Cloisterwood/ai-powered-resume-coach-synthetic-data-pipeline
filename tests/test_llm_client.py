import sys
import types

import instructor

import resume_pipeline.llm_client as llm_client


def test_anthropic_client_uses_bounded_timeout_without_sdk_retries(monkeypatch):
    observed = {}

    class FakeAnthropic:
        def __init__(self, **kwargs):
            observed.update(kwargs)

    monkeypatch.setitem(
        sys.modules, "anthropic", types.SimpleNamespace(Anthropic=FakeAnthropic)
    )
    monkeypatch.setattr(instructor, "from_anthropic", lambda client: object())
    monkeypatch.setattr(llm_client, "_clients", {})
    monkeypatch.setattr(llm_client, "_models", {})
    monkeypatch.setattr(llm_client, "_providers", {})
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    llm_client._build("primary")

    assert observed["timeout"] == 60.0
    assert observed["max_retries"] == 0


def test_judge_tier_uses_its_own_openai_configuration(monkeypatch):
    monkeypatch.setenv("LLM_JUDGE_PROVIDER", "openai")
    monkeypatch.setenv("LLM_JUDGE_MODEL", "gpt-5.4-mini")

    assert llm_client._settings("judge") == ("openai", "gpt-5.4-mini")


def test_gpt5_judge_uses_max_completion_tokens(monkeypatch):
    observed = {}

    class Completions:
        def create(self, **options):
            observed.update(options)
            return "ok"

    class Client:
        class chat:
            completions = Completions()

    monkeypatch.setattr(llm_client, "_clients", {"judge": Client()})
    monkeypatch.setattr(llm_client, "_models", {"judge": "gpt-5.4-mini"})
    monkeypatch.setattr(llm_client, "_providers", {"judge": "openai"})
    monkeypatch.setattr(llm_client, "_last_call", 0.0)

    assert llm_client.generate(str, "system", "user", tier="judge") == "ok"
    assert observed["max_completion_tokens"] == 4096
    assert "max_tokens" not in observed
    assert "temperature" not in observed


def test_gpt5_low_skill_uses_tool_compatible_reasoning_effort(monkeypatch):
    observed = {}

    class Completions:
        def create(self, **options):
            observed.update(options)
            return "ok"

    class Client:
        class chat:
            completions = Completions()

    monkeypatch.setattr(llm_client, "_clients", {"low_skill": Client()})
    monkeypatch.setattr(llm_client, "_models", {"low_skill": "gpt-5.4-mini"})
    monkeypatch.setattr(llm_client, "_providers", {"low_skill": "openai"})
    monkeypatch.setattr(llm_client, "_last_call", 0.0)
    monkeypatch.setenv("LLM_LOW_SKILL_EFFORT", "low")

    assert llm_client.generate(str, "system", "user", tier="low_skill") == "ok"
    assert observed["reasoning_effort"] == "none"
