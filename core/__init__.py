"""
Public package API for the core application layer.

This module exposes the package-level facade used by the Streamlit app so the
UI can import `core` and access LLM and session helpers from one place.
"""

from .llm import (
    AuthError,
    LLMError,
    ModelUnavailableError,
    RateLimitError,
    ServiceError,
    get_available_models,
    get_default_model_id,
    get_model_label,
    is_model_configured,
    stream_response,
)
from .session import (
    append_message,
    clear_all_history,
    clear_history,
    get_active_model,
    get_active_persona,
    get_history,
    init as init_session,
    pop_pending_chip,
    set_active_model,
    set_active_persona,
    set_pending_chip,
)

__all__ = [
    "append_message",
    "AuthError",
    "clear_all_history",
    "clear_history",
    "get_active_model",
    "get_available_models",
    "get_default_model_id",
    "get_active_persona",
    "get_history",
    "get_model_label",
    "init_session",
    "is_model_configured",
    "LLMError",
    "ModelUnavailableError",
    "pop_pending_chip",
    "RateLimitError",
    "ServiceError",
    "set_active_model",
    "set_active_persona",
    "set_pending_chip",
    "stream_response",
]
