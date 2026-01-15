"""Chat interface component for Streamlit."""

import streamlit as st


def render_chat_message(role: str, content: str) -> None:
    """Render a single chat message."""
    with st.chat_message(role):
        st.markdown(content)


def render_chat_history(messages: list[dict[str, str]]) -> None:
    """Render the entire chat history."""
    for msg in messages:
        render_chat_message(msg["role"], msg["content"])
