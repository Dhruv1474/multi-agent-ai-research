"""
Streamlit UI for the Multi-Agent AI Research System.

Run from the project root (same folder as pipeline.py):
    streamlit run app.py
"""

import streamlit as st

from pipeline import run_research_pipeline


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
# WHAT: sets the browser tab title, icon, and makes the content area full width.
# WHY:  must be the FIRST Streamlit command in the script.
# BREAKS IF REMOVED: nothing breaks, but the app renders in a narrow centred
#                    column, which is cramped for long reports.
st.set_page_config(
    page_title="Multi-Agent AI Research",
    page_icon="🔍",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
# WHAT: st.session_state is a dict that survives Streamlit's script reruns.
# WHY:  Streamlit re-executes this whole file on EVERY interaction (button
#       click, typing, expanding a section). Without this, clicking "Download"
#       would re-run the entire 4-agent pipeline and burn API calls again.
# BREAKS IF REMOVED: the app would either lose results instantly or re-run the
#                    pipeline on every click. This is the single most important
#                    block in the file.
if "result" not in st.session_state:
    st.session_state.result = None   # the dict returned by run_research_pipeline
if "topic" not in st.session_state:
    st.session_state.topic = ""      # the topic that produced st.session_state.result
if "error" not in st.session_state:
    st.session_state.error = None    # exception text, if the last run failed


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("About")
    st.markdown(
        """
        Four agents run in sequence:

        1. **Search** — finds recent sources (Tavily)
        2. **Reader** — scrapes the best URL
        3. **Writer** — drafts the report
        4. **Critic** — reviews the draft

        A full run takes roughly 1–2 minutes.
        """
    )

    st.divider()

    # WHAT: clears stored results.
    # WHY:  gives the user an explicit way to reset without restarting the app.
    if st.button("Clear results", use_container_width=True):
        st.session_state.result = None
        st.session_state.topic = ""
        st.session_state.error = None
        st.rerun()


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------
st.title("🔍 Multi-Agent AI Research System")
st.caption("Enter a topic and let the agent pipeline research, write, and critique a report.")

# WHAT: st.form groups the input and button into one submission.
# WHY:  without a form, Streamlit reruns the script on every single keystroke in
#       the text box. The form batches it: nothing happens until submit.
# BREAKS IF REMOVED: the app still works, but reruns far more often than needed.
with st.form("research_form"):
    topic = st.text_input(
        "Research topic",
        placeholder="e.g. Recent advances in multi-agent LLM systems",
    )
    submitted = st.form_submit_button("Run research", type="primary")


# ---------------------------------------------------------------------------
# Run the pipeline
# ---------------------------------------------------------------------------
if submitted:
    if not topic.strip():
        st.warning("Please enter a topic first.")
    else:
        # Reset previous state before a new run.
        st.session_state.result = None
        st.session_state.error = None

        # WHAT: st.status shows a live, collapsible progress box.
        # WHY:  the pipeline prints to the terminal, not the browser, so without
        #       this the user stares at a frozen page for ~2 minutes with no
        #       feedback and assumes the app is broken.
        with st.status("Running the agent pipeline…", expanded=True) as status:
            st.write("Search → Reader → Writer → Critic")
            st.write("Detailed logs are printing in your terminal.")
            try:
                # The single call into your existing, unmodified pipeline.
                st.session_state.result = run_research_pipeline(topic)
                st.session_state.topic = topic
                status.update(label="Research complete", state="complete", expanded=False)
            except Exception as exc:
                # WHAT: catches any agent/API failure and stores it.
                # WHY:  an uncaught exception in Streamlit dumps a raw traceback
                #       and loses all state. This keeps the app usable.
                st.session_state.error = f"{type(exc).__name__}: {exc}"
                status.update(label="Run failed", state="error", expanded=False)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
if st.session_state.error:
    st.error("The pipeline failed.")
    st.code(st.session_state.error, language="text")
    st.caption("Check your terminal for the full traceback, and confirm your .env keys are loaded.")

elif st.session_state.result:
    result = st.session_state.result

    st.success(f"Report ready for: **{st.session_state.topic}**")

    # WHAT: tabs for the four pipeline stages.
    # WHY:  the four outputs are long. Stacking them vertically means endless
    #       scrolling; tabs let the user jump straight to the report.
    tab_report, tab_critic, tab_search, tab_scraped = st.tabs(
        ["📄 Report", "🧐 Critique", "🔎 Search results", "📰 Scraped content"]
    )

    with tab_report:
        st.markdown(result.get("report", "_No report was produced._"))

    with tab_critic:
        st.markdown(result.get("feedback", "_No feedback was produced._"))

    with tab_search:
        st.markdown(result.get("search_results", "_No search results._"))

    with tab_scraped:
        st.markdown(result.get("scraped_content", "_No scraped content._"))

    st.divider()

    # WHAT: builds a markdown file in memory and offers it as a download.
    # WHY:  the whole point of the pipeline is a report the user keeps.
    # NOTE: this button triggers a rerun when clicked — which is exactly why the
    #       result lives in session_state and not in a local variable.
    report_md = (
        f"# Research Report: {st.session_state.topic}\n\n"
        f"{result.get('report', '')}\n\n"
        f"---\n\n"
        f"## Critic Feedback\n\n"
        f"{result.get('feedback', '')}\n"
    )

    # Turn the topic into a safe filename: keep letters/digits, swap the rest for "_".
    safe_name = "".join(
        c if c.isalnum() else "_" for c in st.session_state.topic
    ).strip("_")[:50] or "report"

    st.download_button(
        "⬇️ Download report (.md)",
        data=report_md,
        file_name=f"{safe_name}.md",
        mime="text/markdown",
    )

else:
    st.info("Enter a topic above and click **Run research** to begin.")
