"""Streamlit frontend entrypoint for Citeflow.

This is the Home page. Additional pages (Research Search, AI Summary,
AI Chat, Search History) live under `frontend/pages/` and are picked up
automatically by Streamlit's multipage navigation.
"""

import logging

import streamlit as st

from api_client import API_BASE_URL, ApiError, get_health

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Citeflow",
    page_icon="🔎",
    layout="wide",
)


def render_home() -> None:
    """Render the Home page: project overview and backend status."""
    st.title("🔎 Citeflow")
    st.caption("Automated web research powered by Retrieval-Augmented Generation (RAG)")

    st.markdown(
        """
        Search the web, retrieve the most relevant passages with semantic
        search, and get concise, source-cited AI summaries — all from a
        single query.
        """
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Web Search", "DuckDuckGo")
    col2.metric("Semantic Search", "FAISS + MiniLM")
    col3.metric("LLM", "Groq")
    col4.metric("Framework", "LangChain")

    st.divider()

    st.subheader("Backend Status")
    with st.spinner("Checking backend connection..."):
        try:
            health = get_health()
        except ApiError:
            health = None

    if health and "app_name" in health and "version" in health:
        st.success(f"Connected to **{health['app_name']}** API (v{health['version']}) — status: {health['status']}")
    elif health is not None:
        st.warning(
            f"A server responded at `{API_BASE_URL}` but not with the expected Citeflow "
            "API schema. Is another service running on this port?"
        )
    else:
        st.error(
            f"Could not reach the backend at `{API_BASE_URL}`. "
            "Start it with `uv run uvicorn app.main:app --reload`."
        )

    st.divider()
    st.subheader("Get Started")
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
    nav_col1.markdown("**🔍 Research Search**\n\nSearch the web and scrape sources.")
    nav_col2.markdown("**🧠 AI Summary**\n\nGenerate a cited RAG summary.")
    nav_col3.markdown("**💬 AI Chat**\n\nAsk grounded follow-up questions.")
    nav_col4.markdown("**🕒 Search History**\n\nRevisit and reuse past searches.")
    st.caption("Use the sidebar to navigate between pages.")


if __name__ == "__main__":
    render_home()
