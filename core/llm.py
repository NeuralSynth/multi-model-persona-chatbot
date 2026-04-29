"""
core/llm.py
-----------
Multi-provider LLM integration layer.

Design pattern:
  - Strategy: each provider has its own streaming implementation.
  - Factory: resolves a model selection into the correct provider strategy.

Supported providers:
  - ChatGPT via OpenAI
  - Gemini via Google GenAI
  - DeepSeek via OpenAI-compatible API
  - Self-hosted OpenAI-compatible endpoints
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
import os
import time
from typing import Generator


logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_BACKOFF = 1.0
MODEL_UNAVAILABLE_MESSAGE = "Model unavailable at this time. It is being implemented."


class LLMError(Exception):
    """Base class for all LLM layer errors."""


class RateLimitError(LLMError):
    """Raised when the selected provider rate limits the request."""


class AuthError(LLMError):
    """Raised when the configured credentials are invalid."""


class ServiceError(LLMError):
    """Raised for provider service and connectivity failures."""


class ModelUnavailableError(LLMError):
    """Raised when a selected model is not configured for the current deployment."""


@dataclass(frozen=True)
class ModelOption:
    id: str
    label: str
    provider: str
    default_model: str | None
    api_key_env: str | None = None
    model_env: str | None = None
    base_url: str | None = None
    base_url_env: str | None = None
    requires_api_key: bool = True


MODEL_REGISTRY: dict[str, ModelOption] = {
    "chatgpt": ModelOption(
        id="chatgpt",
        label="ChatGPT",
        provider="openai",
        default_model="gpt-4.1-mini",
        api_key_env="OPENAI_API_KEY",
        model_env="OPENAI_MODEL",
    ),
    "gemini": ModelOption(
        id="gemini",
        label="Gemini",
        provider="gemini",
        default_model="gemini-2.5-flash",
        api_key_env="GEMINI_API_KEY",
        model_env="GEMINI_MODEL",
    ),
    "deepseek": ModelOption(
        id="deepseek",
        label="DeepSeek",
        provider="openai_compatible",
        default_model="deepseek-chat",
        api_key_env="DEEPSEEK_API_KEY",
        model_env="DEEPSEEK_MODEL",
        base_url="https://api.deepseek.com",
    ),
    "self_hosted": ModelOption(
        id="self_hosted",
        label="Self-hosted",
        provider="openai_compatible",
        default_model=None,
        api_key_env="SELF_HOSTED_API_KEY",
        model_env="SELF_HOSTED_MODEL_NAME",
        base_url_env="SELF_HOSTED_BASE_URL",
        requires_api_key=False,
    ),
}

DEFAULT_MODEL_ID = "gemini"


def _clean_env(name: str | None) -> str | None:
    if not name:
        return None
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def get_available_models() -> list[ModelOption]:
    return list(MODEL_REGISTRY.values())


def get_default_model_id() -> str:
    return DEFAULT_MODEL_ID


def get_model_option(model_id: str) -> ModelOption:
    try:
        return MODEL_REGISTRY[model_id]
    except KeyError as exc:
        raise ModelUnavailableError(MODEL_UNAVAILABLE_MESSAGE) from exc


def get_model_label(model_id: str) -> str:
    return get_model_option(model_id).label


def get_resolved_model_name(model_id: str) -> str | None:
    option = get_model_option(model_id)
    if option.model_env:
        return _clean_env(option.model_env) or option.default_model
    return option.default_model


def is_model_configured(model_id: str) -> bool:
    option = get_model_option(model_id)
    if option.requires_api_key and not _clean_env(option.api_key_env):
        return False
    if option.base_url_env and not _clean_env(option.base_url_env):
        return False
    if option.model_env and option.default_model is None and not _clean_env(option.model_env):
        return False
    return True


class BaseLLMStrategy(ABC):
    def _missing_requirements(self, option: ModelOption) -> list[str]:
        missing: list[str] = []
        if option.requires_api_key and option.api_key_env and not _clean_env(option.api_key_env):
            missing.append(option.api_key_env)
        if option.base_url_env and not _clean_env(option.base_url_env):
            missing.append(option.base_url_env)
        if option.model_env and option.default_model is None and not _clean_env(option.model_env):
            missing.append(option.model_env)
        return missing

    def _ensure_configured(self, option: ModelOption) -> None:
        missing = self._missing_requirements(option)
        if missing:
            logger.warning("Model %s is unavailable. Missing configuration: %s", option.id, ", ".join(missing))
            raise ModelUnavailableError(MODEL_UNAVAILABLE_MESSAGE)

    def _resolve_model_name(self, option: ModelOption) -> str:
        model_name = get_resolved_model_name(option.id)
        if not model_name:
            raise ModelUnavailableError(MODEL_UNAVAILABLE_MESSAGE)
        return model_name

    def _classify_provider_error(self, exc: Exception, provider_name: str) -> LLMError:
        status_code = getattr(exc, "status_code", None)
        if status_code == 401:
            return AuthError(f"Invalid credentials for {provider_name}.")
        if status_code == 429:
            return RateLimitError(f"{provider_name} is rate limiting requests right now.")
        if status_code is not None and status_code >= 500:
            return ServiceError(f"{provider_name} is currently having trouble. Please try again shortly.")
        return ServiceError(f"{provider_name} request failed: {exc}")

    @abstractmethod
    def stream_response(
        self,
        option: ModelOption,
        system_prompt: str,
        conversation_history: list[dict],
    ) -> Generator[str, None, None]:
        raise NotImplementedError


class OpenAICompatibleStrategy(BaseLLMStrategy):
    def _build_client(self, option: ModelOption):
        self._ensure_configured(option)
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ModelUnavailableError(MODEL_UNAVAILABLE_MESSAGE) from exc

        api_key = _clean_env(option.api_key_env)
        base_url = _clean_env(option.base_url_env) if option.base_url_env else option.base_url

        client_kwargs = {"api_key": api_key or "local-no-key-required"}
        if base_url:
            client_kwargs["base_url"] = base_url
        return OpenAI(**client_kwargs)

    def stream_response(
        self,
        option: ModelOption,
        system_prompt: str,
        conversation_history: list[dict],
    ) -> Generator[str, None, None]:
        client = self._build_client(option)
        model_name = self._resolve_model_name(option)
        messages = [{"role": "system", "content": system_prompt}, *conversation_history]
        attempt = 0

        while attempt < MAX_RETRIES:
            try:
                stream = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    stream=True,
                )
                for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    text = getattr(delta, "content", None)
                    if text:
                        yield text
                return
            except Exception as exc:
                status_code = getattr(exc, "status_code", None)
                should_retry = status_code == 429 or (status_code is not None and status_code >= 500)
                if should_retry and attempt < MAX_RETRIES - 1:
                    wait = BASE_BACKOFF * (2 ** attempt)
                    logger.warning("%s request failed with status %s. Retrying in %.1fs.", option.label, status_code, wait)
                    time.sleep(wait)
                    attempt += 1
                    continue
                raise self._classify_provider_error(exc, option.label) from exc


class GeminiStrategy(BaseLLMStrategy):
    def _build_client(self, option: ModelOption):
        self._ensure_configured(option)
        try:
            from google import genai
        except ImportError as exc:
            raise ModelUnavailableError(MODEL_UNAVAILABLE_MESSAGE) from exc
        return genai.Client(api_key=_clean_env(option.api_key_env))

    def _build_contents(self, conversation_history: list[dict]) -> list[dict]:
        contents: list[dict] = []
        for message in conversation_history:
            role = "model" if message["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": message["content"]}]})
        return contents

    def stream_response(
        self,
        option: ModelOption,
        system_prompt: str,
        conversation_history: list[dict],
    ) -> Generator[str, None, None]:
        client = self._build_client(option)
        model_name = self._resolve_model_name(option)
        attempt = 0

        try:
            from google.genai import types
        except ImportError as exc:
            raise ModelUnavailableError(MODEL_UNAVAILABLE_MESSAGE) from exc

        while attempt < MAX_RETRIES:
            try:
                stream = client.models.generate_content_stream(
                    model=model_name,
                    contents=self._build_contents(conversation_history),
                    config=types.GenerateContentConfig(system_instruction=system_prompt),
                )
                for chunk in stream:
                    text = getattr(chunk, "text", None)
                    if text:
                        yield text
                return
            except Exception as exc:
                status_code = getattr(exc, "status_code", None)
                should_retry = status_code == 429 or (status_code is not None and status_code >= 500)
                if should_retry and attempt < MAX_RETRIES - 1:
                    wait = BASE_BACKOFF * (2 ** attempt)
                    logger.warning("%s request failed with status %s. Retrying in %.1fs.", option.label, status_code, wait)
                    time.sleep(wait)
                    attempt += 1
                    continue
                raise self._classify_provider_error(exc, option.label) from exc


class LLMStrategyFactory:
    _strategies: dict[str, BaseLLMStrategy] = {
        "openai": OpenAICompatibleStrategy(),
        "openai_compatible": OpenAICompatibleStrategy(),
        "gemini": GeminiStrategy(),
    }

    @classmethod
    def create(cls, model_id: str) -> tuple[BaseLLMStrategy, ModelOption]:
        option = get_model_option(model_id)
        try:
            strategy = cls._strategies[option.provider]
        except KeyError as exc:
            raise ModelUnavailableError(MODEL_UNAVAILABLE_MESSAGE) from exc
        return strategy, option


def stream_response(
    system_prompt: str,
    conversation_history: list[dict],
    model_id: str | None = None,
) -> Generator[str, None, None]:
    strategy, option = LLMStrategyFactory.create(model_id or DEFAULT_MODEL_ID)
    yield from strategy.stream_response(
        option=option,
        system_prompt=system_prompt,
        conversation_history=conversation_history,
    )
