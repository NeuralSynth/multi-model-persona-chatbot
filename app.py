"""
app.py
------
SST Persona Chatbot - main Streamlit entry point.

Architecture:
  - Presentation layer (this file): layout, widgets, event handling
  - Core layer: model strategies + factory (core/llm.py), state (core/session.py)
  - Persona layer: system prompts + metadata (personas/)
"""

from __future__ import annotations

import base64
import html
import mimetypes
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

import core
from personas import PERSONAS


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
AVATAR_DIR = PROJECT_ROOT / "assets" / "avatars"
AVATAR_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

PERSONA_NAMES = list(PERSONAS.keys())
MODEL_OPTIONS = core.get_available_models()
MODEL_OPTION_IDS = [option.id for option in MODEL_OPTIONS]
DEFAULT_PERSONA = PERSONA_NAMES[0]
DEFAULT_MODEL_ID = core.get_default_model_id()

core.init_session(DEFAULT_PERSONA, DEFAULT_MODEL_ID)

st.set_page_config(
    page_title="SST - Persona Chat",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

active_persona_name = core.get_active_persona()
persona_meta = PERSONAS[active_persona_name]
accent = persona_meta["color"]

st.markdown(
    f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');

  html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    background-color: #0A0A0F;
    color: #E8E8EE;
  }}

  section[data-testid="stSidebar"] {{
    background: #0F0F18 !important;
    border-right: 1px solid #1E1E2E;
  }}
  section[data-testid="stSidebar"] > div:first-child {{
    width: min(22rem, 86vw) !important;
  }}
  section[data-testid="stSidebar"] * {{
    color: #E8E8EE !important;
  }}

  #MainMenu, footer, header {{ visibility: hidden; }}
  .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}

  div[data-testid="stButton"] button {{
    background: #13131F;
    border: 1px solid #2A2A40;
    color: #C8C8D8;
    border-radius: 10px;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 0.55rem 1rem;
    width: 100%;
    text-align: left;
    transition: all 0.18s ease;
    margin-bottom: 4px;
  }}
  div[data-testid="stButton"] button:hover {{
    background: #1A1A2E;
    border-color: {accent};
    color: {accent};
    transform: translateX(3px);
  }}

  .active-persona-btn button {{
    background: linear-gradient(135deg, #1A1A2E, #0F0F1A) !important;
    border: 1px solid {accent} !important;
    color: {accent} !important;
    box-shadow: 0 0 12px {accent}33;
  }}

  .chat-message {{
    display: flex;
    gap: 14px;
    margin-bottom: 1.4rem;
    animation: fadeSlideIn 0.25s ease;
  }}
  @keyframes fadeSlideIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}
  .chat-message.user {{ flex-direction: row-reverse; }}
  .chat-avatar {{
    width: 38px;
    height: 38px;
    border-radius: 50%;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    flex-shrink: 0;
    border: 1px solid #2A2A40;
    background: #13131F;
  }}
  .chat-message.user .chat-avatar {{
    background: {accent}22;
    border-color: {accent}55;
  }}
  .chat-avatar img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }}
  .chat-bubble {{
    max-width: 72%;
    padding: 0.85rem 1.1rem;
    border-radius: 14px;
    line-height: 1.65;
    font-size: 0.93rem;
  }}
  .chat-message.assistant .chat-bubble {{
    background: #13131F;
    border: 1px solid #1E1E30;
    border-top-left-radius: 4px;
    color: #DDDDE8;
  }}
  .chat-message.user .chat-bubble {{
    background: {accent}18;
    border: 1px solid {accent}44;
    border-top-right-radius: 4px;
    color: #F0F0F8;
  }}
  .thinking-indicator {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    margin-left: 0.45rem;
    color: rgba(232, 232, 238, 0.48);
    font-size: 0.74rem;
    letter-spacing: 0.02em;
    vertical-align: middle;
  }}
  .thinking-loop {{
    font-size: 0.9rem;
    opacity: 0.7;
  }}

  .chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 0.8rem 0 1rem; }}
  .chip-row div[data-testid="stButton"] button {{
    background: #13131F;
    border: 1px solid {accent}55;
    color: {accent};
    border-radius: 20px;
    font-size: 0.78rem;
    padding: 0.3rem 0.9rem;
    width: auto;
    white-space: nowrap;
  }}
  .chip-row div[data-testid="stButton"] button:hover {{
    background: {accent}18;
    border-color: {accent};
    transform: none;
  }}

  div[data-testid="stChatInput"] {{
    background: #13131F !important;
    border: 1px solid #2A2A40 !important;
    border-radius: 12px !important;
  }}
  div[data-testid="stChatInput"]:focus-within {{
    border-color: {accent} !important;
    box-shadow: 0 0 0 2px {accent}22 !important;
  }}

  .persona-header {{
    background: linear-gradient(135deg, #13131F 0%, #0F0F18 100%);
    border: 1px solid #1E1E30;
    border-left: 3px solid {accent};
    border-radius: 12px;
    padding: 1rem 1.3rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
  }}
  .persona-header-avatar {{
    width: 56px;
    height: 56px;
  }}
  .persona-header-name {{
    font-family: 'Syne', sans-serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: {accent};
    margin: 0;
  }}
  .persona-header-title {{
    font-size: 0.78rem;
    color: #888;
    margin: 2px 0 0;
  }}
  .persona-header-tagline {{
    font-size: 0.82rem;
    color: #AAABB8;
    margin: 4px 0 0;
    font-style: italic;
  }}

  .empty-state {{
    text-align: center;
    padding: 3rem 1rem;
    color: #444;
  }}
  .empty-state-text {{
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    color: #555;
  }}

  .sidebar-logo {{
    font-family: 'Syne', sans-serif;
    font-size: 1.4rem;
    font-weight: 800;
    color: {accent};
    letter-spacing: -0.5px;
    margin-bottom: 0.2rem;
  }}
  .sidebar-sub {{
    font-size: 0.72rem;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 1.5rem;
  }}

  hr {{ border-color: #1E1E2E !important; }}

  @media (max-width: 1024px) {{
    .block-container {{
      padding-left: 1rem;
      padding-right: 1rem;
    }}
    .chat-bubble {{
      max-width: 82%;
    }}
  }}

  @media (max-width: 768px) {{
    section[data-testid="stSidebar"] > div:first-child {{
      width: min(20rem, 88vw) !important;
    }}
    .block-container {{
      padding-top: 1rem;
      padding-left: 0.85rem;
      padding-right: 0.85rem;
      padding-bottom: 1.25rem;
    }}
    .persona-header {{
      padding: 0.9rem 1rem;
      gap: 0.85rem;
      align-items: flex-start;
    }}
    .persona-header-avatar {{
      width: 48px;
      height: 48px;
    }}
    .persona-header-name {{
      font-size: 1.05rem;
    }}
    .persona-header-title {{
      font-size: 0.74rem;
    }}
    .persona-header-tagline {{
      font-size: 0.78rem;
      line-height: 1.45;
    }}
    .chat-message {{
      gap: 10px;
      margin-bottom: 1rem;
    }}
    .chat-avatar {{
      width: 34px;
      height: 34px;
    }}
    .chat-bubble {{
      max-width: calc(100% - 48px);
      padding: 0.75rem 0.9rem;
      font-size: 0.89rem;
      line-height: 1.55;
    }}
    .chip-row {{
      gap: 6px;
      margin-top: 0.65rem;
    }}
    .chip-row div[data-testid="stButton"] button {{
      width: 100%;
      white-space: normal;
      text-align: left;
      border-radius: 14px;
      line-height: 1.35;
      min-height: 44px;
      padding: 0.55rem 0.8rem;
    }}
    div[data-testid="stChatInput"] {{
      border-radius: 14px !important;
    }}
    div[data-testid="stButton"] button {{
      min-height: 44px;
    }}
  }}

  @media (max-width: 520px) {{
    section[data-testid="stSidebar"] > div:first-child {{
      width: 100vw !important;
    }}
    .block-container {{
      padding-left: 0.7rem;
      padding-right: 0.7rem;
    }}
    .sidebar-logo {{
      font-size: 1.15rem;
    }}
    .sidebar-sub {{
      font-size: 0.66rem;
      letter-spacing: 1.1px;
    }}
    .persona-header {{
      flex-direction: column;
      align-items: flex-start;
      gap: 0.7rem;
      padding: 0.85rem 0.9rem;
    }}
    .persona-header-avatar {{
      width: 44px;
      height: 44px;
    }}
    .persona-header-name {{
      font-size: 0.98rem;
    }}
    .persona-header-title,
    .persona-header-tagline,
    .empty-state-text {{
      font-size: 0.76rem;
    }}
    .chat-message {{
      gap: 8px;
    }}
    .chat-avatar {{
      width: 30px;
      height: 30px;
      font-size: 0.9rem;
    }}
    .chat-bubble {{
      max-width: calc(100% - 40px);
      padding: 0.7rem 0.82rem;
      font-size: 0.85rem;
      border-radius: 12px;
    }}
    div[data-testid="stButton"] button {{
      font-size: 0.8rem;
      padding: 0.5rem 0.85rem;
    }}
    .chip-row div[data-testid="stButton"] button {{
      font-size: 0.74rem;
      min-height: 42px;
    }}
  }}
</style>
""",
    unsafe_allow_html=True,
)


def _find_avatar_path(image_name: str) -> Path | None:
    for extension in AVATAR_EXTENSIONS:
        candidate = AVATAR_DIR / f"{image_name}{extension}"
        if candidate.exists():
            return candidate
    return None


def _build_avatar_markup(image_name: str, alt_text: str) -> str:
    avatar_path = _find_avatar_path(image_name)
    if avatar_path is None:
        initials = "".join(part[0] for part in alt_text.split()[:2]).upper()
        return f"<span>{initials}</span>"

    mime_type, _ = mimetypes.guess_type(avatar_path.name)
    if mime_type is None:
        mime_type = "image/png"
    image_data = base64.b64encode(avatar_path.read_bytes()).decode("ascii")
    return f'<img src="data:{mime_type};base64,{image_data}" alt="{alt_text}" />'


def _message_markup(role: str, content: str, persona_avatar: str) -> str:
    avatar = persona_avatar if role == "assistant" else "🧑"
    css_class = f"chat-message {role}"
    safe_content = html.escape(content).replace("\n", "<br>")
    return f"""
    <div class="{css_class}">
      <div class="chat-avatar">{avatar}</div>
      <div class="chat-bubble">{safe_content}</div>
    </div>
    """


def render_message(role: str, content: str, persona_avatar: str) -> None:
    st.markdown(_message_markup(role, content, persona_avatar), unsafe_allow_html=True)


def handle_user_input(user_text: str) -> None:
    persona_name = core.get_active_persona()
    active_model_id = core.get_active_model()
    meta = PERSONAS[persona_name]
    persona_avatar = _build_avatar_markup(meta["avatar_image_name"], persona_name)

    core.append_message(persona_name, active_model_id, "user", user_text)
    history = core.get_history(persona_name, active_model_id)
    full_response = ""
    user_markup = _message_markup("user", user_text, persona_avatar)

    try:
        placeholder = st.empty()
        placeholder.markdown(user_markup, unsafe_allow_html=True)
        stream = core.stream_response(
            system_prompt=meta["prompt"],
            conversation_history=history[:-1] + [{"role": "user", "content": user_text}],
            model_id=active_model_id,
        )
        for chunk in stream:
            full_response += chunk
            safe_response = html.escape(full_response).replace("\n", "<br>")
            placeholder.markdown(
                f"""
                {user_markup}
                <div class="chat-message assistant">
                  <div class="chat-avatar">{persona_avatar}</div>
                  <div class="chat-bubble">{safe_response}<span class="thinking-indicator"><span class="thinking-loop">◌</span><span>Thinking</span></span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        placeholder.markdown(
            f"""
            {user_markup}
            <div class="chat-message assistant">
              <div class="chat-avatar">{persona_avatar}</div>
              <div class="chat-bubble">{html.escape(full_response).replace("\n", "<br>")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except core.ModelUnavailableError:
        st.error("Model unavailable at this time. It is being implemented.")
        return
    except core.AuthError:
        st.error("The selected model credentials are invalid right now.")
        return
    except core.RateLimitError:
        st.error("You've hit the rate limit. Please wait a moment and try again.")
        return
    except core.ServiceError as exc:
        st.error(f"Service error: {exc}")
        return

    core.append_message(persona_name, active_model_id, "assistant", full_response)


with st.sidebar:
    st.markdown('<div class="sidebar-logo">SST Chat</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Multi-Model Persona Chatbot</div>', unsafe_allow_html=True)
    st.markdown("**Choose a persona**")
    st.markdown("")

    for name in PERSONA_NAMES:
        is_active = name == active_persona_name
        if is_active:
            st.markdown('<div class="active-persona-btn">', unsafe_allow_html=True)
        if st.button(name, key=f"persona_btn_{name}"):
            if name != active_persona_name:
                core.set_active_persona(name)
                st.rerun()
        if is_active:
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Clear conversation", key="clear_btn"):
        core.clear_history(core.get_active_persona(), core.get_active_model())
        st.rerun()

    st.markdown("---")
    st.markdown(
        f"""
        <div style="font-size:0.72rem; color:#444; line-height:1.6;">
          <b style="color:#666">Model</b><br>{core.get_model_label(core.get_active_model())}<br><br>
          <b style="color:#666">Status</b><br>{"Available" if core.is_model_configured(core.get_active_model()) else "Unavailable"}<br><br>
          <b style="color:#666">Active</b><br>{active_persona_name}
        </div>
        """,
        unsafe_allow_html=True,
    )


persona_name = core.get_active_persona()
active_model_id = core.get_active_model()
meta = PERSONAS[persona_name]
persona_avatar = _build_avatar_markup(meta["avatar_image_name"], persona_name)

topbar_left, topbar_middle, topbar_right = st.columns([2.2, 2.2, 1])
with topbar_left:
    selected_persona = st.selectbox(
        "Persona",
        PERSONA_NAMES,
        index=PERSONA_NAMES.index(persona_name),
        label_visibility="collapsed",
        key="persona_select_top",
    )
    if selected_persona != persona_name:
        core.set_active_persona(selected_persona)
        st.rerun()

with topbar_middle:
    selected_model = st.selectbox(
        "Model",
        MODEL_OPTION_IDS,
        index=MODEL_OPTION_IDS.index(active_model_id),
        format_func=core.get_model_label,
        label_visibility="collapsed",
        key="model_select_top",
    )
    if selected_model != active_model_id:
        core.set_active_model(selected_model)
        st.rerun()

with topbar_right:
    if st.button("Clear", key="clear_btn_top", use_container_width=True):
        core.clear_history(persona_name, active_model_id)
        st.rerun()

st.markdown(
    f"""
    <div class="persona-header">
      <div class="chat-avatar persona-header-avatar">{persona_avatar}</div>
      <div>
        <p class="persona-header-name">{persona_name}</p>
        <p class="persona-header-title">{meta['title']}</p>
        <p class="persona-header-tagline">{meta['tagline']}</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

history = core.get_history(persona_name, active_model_id)

if not history:
    st.markdown(
        f"""
        <div class="empty-state">
          <div style="display:flex; justify-content:center; margin-bottom:0.5rem;">
            <div class="chat-avatar persona-header-avatar">{persona_avatar}</div>
          </div>
          <p class="empty-state-text">Start a conversation with {persona_name.split()[0]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    for msg in history:
        render_message(msg["role"], msg["content"], persona_avatar)

if not history:
    st.markdown('<div class="chip-row">', unsafe_allow_html=True)
    cols = st.columns(len(meta["chips"]))
    for i, chip_text in enumerate(meta["chips"]):
        with cols[i]:
            if st.button(chip_text, key=f"chip_{active_model_id}_{persona_name}_{i}"):
                core.set_pending_chip(chip_text)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

pending = core.pop_pending_chip()
if pending:
    handle_user_input(pending)

user_input = st.chat_input(
    placeholder=f"Ask {persona_name.split()[0]} something...",
    key=f"chat_input_{active_model_id}_{persona_name}",
)
if user_input and user_input.strip():
    handle_user_input(user_input.strip())
