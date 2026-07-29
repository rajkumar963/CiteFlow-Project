"""Research Search page: run a web search + scrape query against the backend."""

import streamlit as st

from api_client import ApiError, run_search

st.set_page_config(page_title="Research Search | Citeflow", page_icon="🔍", layout="wide")

st.title("🔍 Research Search")
st.caption("Search the web, scrape the top results, and inspect the cleaned source content.")

if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

with st.form("search_form"):
    query = st.text_input("Research question or topic", placeholder="e.g. What is retrieval-augmented generation?")
    max_results = st.slider("Number of sources to retrieve", min_value=1, max_value=10, value=8)
    submitted = st.form_submit_button("Search", use_container_width=True)

if submitted:
    if not query or len(query.strip()) < 3:
        st.warning("Please enter a research question with at least 3 characters.")
    else:
        with st.spinner(f"Searching the web and scraping top {max_results} results..."):
            try:
                result = run_search(query.strip(), max_results=max_results)
                st.session_state.last_result = result
                st.session_state.search_history.insert(0, {"query": result["query"], "search_id": result["search_id"]})
            except ApiError as exc:
                st.session_state.last_result = None
                st.error(f"Search failed: {exc}")

result = st.session_state.last_result
if result:
    st.divider()
    st.subheader(f"Results for: _{result['query']}_")

    scraped_count = sum(1 for source in result["sources"] if source["scraped"])
    col1, col2 = st.columns(2)
    col1.metric("Sources found", result["total_sources"])
    col2.metric("Successfully scraped", scraped_count)

    st.caption(f"Search ID: `{result['search_id']}` — reused by AI Summary and AI Chat.")

    for i, source in enumerate(result["sources"], start=1):
        status_icon = "✅" if source["scraped"] else "⚠️"
        with st.expander(f"{status_icon} {i}. {source['title']} ({source['word_count']} words)"):
            st.markdown(f"**Source:** [{source['url']}]({source['url']})")
            if source["snippet"]:
                st.markdown(f"*{source['snippet']}*")
            if source["scraped"]:
                st.text_area("Cleaned content", source["content"], height=200, key=f"content_{i}")
            else:
                st.warning("This page could not be scraped (blocked, non-HTML, or too little content).")

if st.session_state.search_history:
    st.divider()
    with st.expander(f"Session search history ({len(st.session_state.search_history)})"):
        for entry in st.session_state.search_history:
            st.markdown(f"- `{entry['search_id']}` — {entry['query']}")
