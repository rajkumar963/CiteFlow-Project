"""AI Summary page: generate a cited RAG summary from a prior search."""

import streamlit as st

from api_client import ApiError, run_summary

st.set_page_config(page_title="AI Summary | Citeflow", page_icon="🧠", layout="wide")

st.title("🧠 AI Summary")
st.caption("Retrieve the most relevant passages from a search and generate a grounded, cited summary.")

if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "last_summary" not in st.session_state:
    st.session_state.last_summary = None

if not st.session_state.search_history:
    st.info("Run a query on the **Research Search** page first to generate a `search_id`.")

with st.form("summary_form"):
    history_options = {f"{e['query']} — {e['search_id']}": e["search_id"] for e in st.session_state.search_history}
    if history_options:
        choice = st.selectbox("Select a previous search", options=list(history_options.keys()))
        selected_search_id = history_options[choice]
    else:
        selected_search_id = ""

    manual_search_id = st.text_input("...or paste a search_id directly", value=selected_search_id)
    focus_query = st.text_input("Focus question (optional — defaults to the original search query)")
    top_k = st.slider("Number of passages to retrieve", min_value=1, max_value=20, value=6)
    submitted = st.form_submit_button("Generate Summary", use_container_width=True)

if submitted:
    if not manual_search_id.strip():
        st.warning("Please select or enter a search_id.")
    else:
        with st.spinner("Retrieving relevant passages and generating summary..."):
            try:
                st.session_state.last_summary = run_summary(
                    manual_search_id.strip(),
                    focus_query=focus_query.strip() or None,
                    top_k=top_k,
                )
            except ApiError as exc:
                st.session_state.last_summary = None
                st.error(f"Summary generation failed: {exc}")

summary = st.session_state.last_summary
if summary:
    st.divider()
    st.subheader(f"Summary for: _{summary['query']}_")

    st.markdown("### 📄 Research Summary")
    st.success(summary["summary"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 💡 Key Insights")
        for item in summary["key_insights"]:
            st.markdown(f"- {item}")
    with col2:
        st.markdown("#### 📊 Important Facts")
        for item in summary["important_facts"]:
            st.markdown(f"- {item}")
    with col3:
        st.markdown("#### ✅ Actionable Takeaways")
        for item in summary["actionable_takeaways"]:
            st.markdown(f"- {item}")

    st.divider()
    st.markdown("### 🔗 Cited Passages")
    for i, citation in enumerate(summary["citations"], start=1):
        with st.expander(f"[{i}] {citation['source_title']} — relevance {citation['relevance_score']:.2f}"):
            st.markdown(f"**Source:** [{citation['source_url']}]({citation['source_url']})")
            st.write(citation["text"])
