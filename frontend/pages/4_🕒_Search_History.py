"""Search History page: browse recent searches processed by the backend."""

import streamlit as st

from api_client import ApiError, get_history

st.set_page_config(page_title="Search History | Citeflow", page_icon="🕒", layout="wide")

st.title("🕒 Search History")
st.caption("Recent research searches processed by the backend, most recent first.")

if "search_history" not in st.session_state:
    st.session_state.search_history = []


def _remember_locally(query: str, search_id: str) -> None:
    """Add a search to the session-local dropdown used by the other pages."""
    entry = {"query": query, "search_id": search_id}
    if entry not in st.session_state.search_history:
        st.session_state.search_history.insert(0, entry)


limit = st.slider("Number of recent searches to show", min_value=5, max_value=100, value=20, step=5)

try:
    history = get_history(limit=limit)
except ApiError as exc:
    st.error(f"Could not load search history: {exc}")
    history = None

if history is not None:
    items = history["items"]
    if not items:
        st.info("No searches yet. Run a query on the **Research Search** page first.")
    else:
        st.caption(f"Showing {len(items)} of {history['total']} recent searches known to the backend.")
        for item in items:
            with st.container(border=True):
                cols = st.columns([4, 2, 2, 1, 1])
                cols[0].markdown(f"**{item['query']}**")
                cols[0].caption(f"`{item['search_id']}`")
                cols[1].caption(item["created_at"])
                cols[2].caption(f"{item['scraped_sources']}/{item['total_sources']} sources scraped")

                if cols[3].button("Summary", key=f"summary_{item['search_id']}", use_container_width=True):
                    _remember_locally(item["query"], item["search_id"])
                    st.switch_page("pages/2_🧠_AI_Summary.py")

                if cols[4].button("Chat", key=f"chat_{item['search_id']}", use_container_width=True):
                    _remember_locally(item["query"], item["search_id"])
                    st.switch_page("pages/3_💬_AI_Chat.py")
