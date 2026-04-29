"""
core/session.py
---------------
Centralized Streamlit session-state management.

Conversation history is isolated per persona and per model.
"""

from __future__ import annotations

import streamlit as st


_KEY_PERSONA = "active_persona"
_KEY_MODEL = "active_model"
_KEY_HISTORY = "conversation_history"
_KEY_PENDING_CHIP = "pending_chip"


def init(default_persona: str, default_model: str) -> None:
    if _KEY_PERSONA not in st.session_state:
        st.session_state[_KEY_PERSONA] = default_persona
    if _KEY_MODEL not in st.session_state:
        st.session_state[_KEY_MODEL] = default_model
    if _KEY_HISTORY not in st.session_state:
        st.session_state[_KEY_HISTORY] = {}
    if _KEY_PENDING_CHIP not in st.session_state:
        st.session_state[_KEY_PENDING_CHIP] = None


def get_active_persona() -> str:
    return st.session_state[_KEY_PERSONA]


def set_active_persona(name: str) -> None:
    st.session_state[_KEY_PERSONA] = name


def get_active_model() -> str:
    return st.session_state[_KEY_MODEL]


def set_active_model(model_id: str) -> None:
    st.session_state[_KEY_MODEL] = model_id


def _history_key(persona_name: str, model_id: str) -> str:
    return f"{model_id}:{persona_name}"


def get_history(persona_name: str, model_id: str) -> list[dict]:
    history_map: dict = st.session_state[_KEY_HISTORY]
    key = _history_key(persona_name, model_id)
    if key not in history_map:
        history_map[key] = []
    return history_map[key]


def append_message(persona_name: str, model_id: str, role: str, content: str) -> None:
    get_history(persona_name, model_id).append({"role": role, "content": content})


def clear_history(persona_name: str, model_id: str) -> None:
    st.session_state[_KEY_HISTORY][_history_key(persona_name, model_id)] = []


def clear_all_history() -> None:
    st.session_state[_KEY_HISTORY] = {}


def set_pending_chip(text: str | None) -> None:
    st.session_state[_KEY_PENDING_CHIP] = text


def pop_pending_chip() -> str | None:
    value = st.session_state[_KEY_PENDING_CHIP]
    st.session_state[_KEY_PENDING_CHIP] = None
    return value
