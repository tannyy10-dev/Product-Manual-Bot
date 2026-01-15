"""Source citations display component."""

import streamlit as st


def render_sources(sources: list[dict]) -> None:
    """
    Render source citations in an expandable section.

    Args:
        sources: List of source dictionaries with document_name, page_number, etc.
    """
    if not sources:
        return

    with st.expander("📚 View Sources", expanded=False):
        for idx, source in enumerate(sources, 1):
            doc_name = source.get("document_name", "Unknown")
            page_num = source.get("page_number")
            section = source.get("section_title")
            similarity = source.get("similarity", 0.0)

            # Format source information
            source_text = f"**{idx}. {doc_name}**"
            if section:
                source_text += f" - {section}"
            if page_num:
                source_text += f" (Page {page_num})"

            # Add similarity score as a badge
            similarity_pct = int(similarity * 100)
            source_text += f" `{similarity_pct}% match`"

            st.markdown(source_text)
