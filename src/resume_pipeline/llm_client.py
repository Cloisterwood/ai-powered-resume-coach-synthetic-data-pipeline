"""Provider-swappable Instructor client with primary and low-skill tiers."""

import os
import time
from typing import Any, Literal

import instructor
from dotenv import load_dotenv

load_dotenv()

Tier = Literal["primary", "low_skill", "judge"]

_RATE_LIMIT_SECONDS = 0.5
_REQUEST_TIMEOUT_SECONDS = 60.0
_last_call = 0.0
_clients: dict[Tier, Any] = {}
_models: dict[Tier, str] = {}
_providers: dict[Tier, str] = {}
_models_without_temperature: set[tuple[str, str]] = set()

_PROVIDER_BASE_URLS = {
    "groq": "https://api.groq.com/openai/v1",
    "openai": None,
    "openrouter": "https://openrouter.ai/api/v1",
}


def _settings(tier: Tier) -> tuple[str, str]:
    if tier == "primary":
        return (
            os.getenv("LLM_PROVIDER", "anthropic").lower(),
            os.getenv("LLM_MODEL", "claude-sonnet-5"),
        )
    if tier == "low_skill":
        return (
            os.getenv("LLM_LOW_SKILL_PROVIDER", "openai").lower(),
            os.getenv("LLM_LOW_SKILL_MODEL", "gpt-5.4-mini"),
        )
    if tier == "judge":
        return (
            os.getenv("LLM_JUDGE_PROVIDER", "openai").lower(),
            os.getenv("LLM_JUDGE_MODEL", "gpt-5.4-mini"),
        )
    raise ValueError(f"unknown LLM tier {tier!r}")


def _build(tier: Tier) -> None:
    """Build and cache the Instructor client configured for one model tier."""
    provider, model = _settings(tier)
    if provider == "anthropic":
        from anthropic import Anthropic

        client = instructor.from_anthropic(
            Anthropic(timeout=_REQUEST_TIMEOUT_SECONDS, max_retries=0)
        )
    elif provider in _PROVIDER_BASE_URLS:
        from openai import OpenAI

        api_key = os.getenv(f"{provider.upper()}_API_KEY")
        if not api_key:
            raise RuntimeError(
                f"{provider.upper()}_API_KEY is required for the {tier} LLM tier"
            )
        client = instructor.from_openai(
            OpenAI(
                base_url=_PROVIDER_BASE_URLS[provider],
                api_key=api_key,
                timeout=_REQUEST_TIMEOUT_SECONDS,
                max_retries=0,
            )
        )
    else:
        raise ValueError(f"unknown LLM provider {provider!r}")

    _clients[tier] = client
    _models[tier] = model
    _providers[tier] = provider


def _token_limit_option(provider: str, model: str) -> str:
    """Return the token-limit parameter accepted by the configured provider/model."""
    if provider == "openai" and model.lower().startswith("gpt-5"):
        return "max_completion_tokens"
    return "max_tokens"


def _supports_temperature(provider: str, model: str) -> bool:
    """GPT-5 models use their fixed default temperature."""
    return not (provider == "openai" and model.lower().startswith("gpt-5"))


def _reasoning_effort(provider: str, model: str) -> str:
    """Use the only tool-compatible reasoning setting for GPT-5 chat completions."""
    if provider == "openai" and model.lower().startswith("gpt-5"):
        return "none"
    return os.getenv("LLM_LOW_SKILL_EFFORT", "low")


def generate(
    response_model: type[Any],
    system: str,
    user: str,
    temperature: float = 0.9,
    max_tokens: int = 4096,
    tier: Tier = "primary",
) -> Any:
    """Make one structured LLM call with rate limiting and Instructor retries."""
    global _last_call

    if tier not in _clients:
        _build(tier)

    wait = _RATE_LIMIT_SECONDS - (time.time() - _last_call)
    if wait > 0:
        time.sleep(wait)

    model_identity = (_providers[tier], _models[tier])
    options: dict[str, Any] = {
        "model": _models[tier],
        "response_model": response_model,
        "max_retries": 2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    options[_token_limit_option(_providers[tier], _models[tier])] = max_tokens
    if tier == "low_skill" and _providers[tier] == "openai":
        options["reasoning_effort"] = _reasoning_effort(
            _providers[tier], _models[tier]
        )

    if (
        model_identity not in _models_without_temperature
        and _supports_temperature(_providers[tier], _models[tier])
    ):
        options["temperature"] = temperature

    try:
        result = _clients[tier].chat.completions.create(**options)
    except Exception as error:
        message = str(error).lower()
        rejects_temperature = "temperature" in message and "deprecated" in message
        if model_identity in _models_without_temperature or not rejects_temperature:
            raise
        _models_without_temperature.add(model_identity)
        options.pop("temperature", None)
        result = _clients[tier].chat.completions.create(**options)

    _last_call = time.time()
    return result
