"""AI Chat page: ask follow-up questions grounded in a prior search's sources."""

import streamlit as st

from api_client import ApiError, run_chat

st.set_page_config(page_title="AI Chat | Citeflow", page_icon="💬", layout="wide")

st.title("💬 AI Chat")
st.caption("Ask follow-up questions grounded in the sources from a prior search.")

if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "chat_transcripts" not in st.session_state:
    st.session_state.chat_transcripts = {}
if "chat_citations" not in st.session_state:
    st.session_state.chat_citations = {}

if not st.session_state.search_history:
    st.info("Run a query on the **Research Search** page first to generate a `search_id`.")

history_options = {f"{e['query']} — {e['search_id']}": e["search_id"] for e in st.session_state.search_history}
if history_options:
    choice = st.selectbox("Select a previous search", options=list(history_options.keys()))
    default_search_id = history_options[choice]
else:
    default_search_id = ""

search_id = st.text_input("...or paste a search_id directly", value=default_search_id)

if search_id:
    transcript = st.session_state.chat_transcripts.get(search_id, [])
    for turn in transcript:
        with st.chat_message(turn["role"]):
            st.write(turn["content"])

    if question := st.chat_input("Ask a follow-up question about this search..."):
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = run_chat(search_id, question)
                    st.session_state.chat_transcripts[search_id] = result["history"]
                    st.session_state.chat_citations[search_id] = result["citations"]
                    st.write(result["answer"])
                except ApiError as exc:
                    st.error(f"Chat request failed: {exc}")

    citations = st.session_state.chat_citations.get(search_id)
    if citations:
        st.divider()
        with st.expander(f"🔗 Sources used in the last answer ({len(citations)})"):
            for i, citation in enumerate(citations, start=1):
                st.markdown(f"**[{i}] {citation['source_title']}** — relevance {citation['relevance_score']:.2f}")
                st.markdown(f"[{citation['source_url']}]({citation['source_url']})")
                st.caption(citation["text"][:300] + ("..." if len(citation["text"]) > 300 else ""))
else:
    st.warning("Please select or enter a search_id to start chatting.")
