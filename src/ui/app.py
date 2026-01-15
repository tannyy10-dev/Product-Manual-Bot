"""Streamlit frontend application."""

import json
import os

import httpx
import streamlit as st

from src.ui.components.chat_interface import render_chat_history, render_chat_message
from src.ui.components.source_citations import render_sources

# Page configuration
st.set_page_config(
    page_title="Product Manual Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for professional styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .stChatMessage {
        padding: 1rem;
    }
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "sources" not in st.session_state:
    st.session_state.sources = []

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
STREAM_ENDPOINT = f"{API_BASE_URL}/api/v1/chat/stream"
UPLOAD_ENDPOINT = f"{API_BASE_URL}/api/v1/ingestion/upload"

# Sidebar for document upload
with st.sidebar:
    st.header("Document Management")
    st.markdown("Upload product manuals in PDF format to add them to the knowledge base.")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload a product manual PDF to be processed and indexed",
    )

    if uploaded_file is not None:
        if st.button("Upload Document", type="primary"):
            with st.spinner("Uploading document..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    response = httpx.post(UPLOAD_ENDPOINT, files=files, timeout=30.0)

                    if response.status_code == 202:
                        st.success(f"{uploaded_file.name} uploaded successfully!")
                        st.info("Document is being processed in the background. It will be available shortly.")
                    else:
                        st.error(f"Upload failed: {response.text}")
                except Exception as e:
                    st.error(f"Error uploading file: {str(e)}")

    st.markdown("---")
    st.markdown("### About")
    st.markdown(
        """
        This bot uses RAG (Retrieval-Augmented Generation) to answer
        questions based on uploaded product manuals. It provides
        source citations for transparency.
        """
    )

# Main content area
st.markdown('<div class="main-header">🤖 Product Manual Bot</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Ask questions about your product manuals and get accurate, cited answers</div>',
    unsafe_allow_html=True,
)

# Display chat history
render_chat_history(st.session_state.messages)

# Chat input
if prompt := st.chat_input("Ask about the product..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    render_chat_message("user", prompt)

    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        sources = []

        try:
            chat_request = {
                "messages": st.session_state.messages[:-1],  # Exclude current message
                "query": prompt,
            }

            # Use streaming context safely
            with httpx.stream("POST", STREAM_ENDPOINT, json=chat_request, timeout=120.0) as response:
                if response.status_code != 200:
                    message_placeholder.markdown(f"API Error: Status code {response.status_code}")
                else:
                    buffer = ""
                    # Iterate over streamed lines
                    for line in response.iter_lines():
                        if not line:
                            # Empty line indicates end of SSE event
                            if buffer:
                                event_data = None
                                # Extract JSON data from SSE
                                for event_line in buffer.strip().split("\n"):
                                    if event_line.startswith("data: "):
                                        try:
                                            event_data = json.loads(event_line[6:])
                                        except json.JSONDecodeError:
                                            continue

                                if event_data:
                                    event_type = event_data.get("type")
                                    if event_type == "chunk":
                                        chunk = event_data.get("content", "")
                                        full_response += chunk
                                        message_placeholder.markdown(full_response + "▌")
                                    elif event_type == "sources":
                                        sources = event_data.get("sources", [])
                                        st.session_state.sources = sources
                                    elif event_type == "done":
                                        message_placeholder.markdown(full_response)
                                    elif event_type == "error":
                                        st.error(event_data.get("message", "Unknown error"))

                                buffer = ""
                            continue

                        # Accumulate line
                        buffer += line + "\n"

        except httpx.ReadTimeout:
            st.warning("Request timed out. Partial response received.")
            if full_response:
                message_placeholder.markdown(full_response)
        except httpx.ReadError as e:
            # Handle connection closed early
            error_msg = str(e).lower()
            if "incomplete chunked read" in error_msg or "peer closed" in error_msg:
                st.warning("Connection closed early. Partial response may be available.")
                if full_response:
                    message_placeholder.markdown(full_response)
            else:
                st.error(f"Connection error: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            if full_response:
                message_placeholder.markdown(full_response)

        # Append assistant response to session state
        st.session_state.messages.append({"role": "assistant", "content": full_response})

        # Render sources if available
        if sources:
            render_sources(sources)


# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #666; font-size: 0.9rem;">'
    "Powered by FastAPI, Groq, and Neon DB"
    "</div>",
    unsafe_allow_html=True,
)
