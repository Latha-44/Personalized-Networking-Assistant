"""
app.py
------
Streamlit frontend for the Personalized Networking Assistant.

Run with:
    streamlit run frontend/app.py

Talks to the FastAPI backend over HTTP (set API_BASE_URL below or via the
API_BASE_URL environment variable if the backend runs somewhere other than
localhost:8000).
"""

import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Personalized Networking Assistant",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .main { background-color: #0f1116; }
        .starter-card {
            background: linear-gradient(135deg, #1e2530, #232b3a);
            border: 1px solid #33415c;
            border-radius: 12px;
            padding: 18px 20px;
            margin-bottom: 14px;
            font-size: 1.02rem;
            line-height: 1.5;
        }
        .theme-pill {
            display: inline-block;
            background-color: #3b82f6;
            color: white;
            border-radius: 999px;
            padding: 4px 14px;
            margin: 3px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .fact-box {
            background-color: #16221a;
            border-left: 4px solid #22c55e;
            border-radius: 6px;
            padding: 14px 18px;
            margin-top: 10px;
        }
        h1, h2, h3 { font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.title("🤝 Networking Assistant")
page = st.sidebar.radio("Navigate", ["✨ Generate Starters", "🔍 Fact Check", "🕓 History"])
st.sidebar.markdown("---")
st.sidebar.caption(f"Backend: `{API_BASE_URL}`")

if "last_interaction_id" not in st.session_state:
    st.session_state.last_interaction_id = None
if "last_starters" not in st.session_state:
    st.session_state.last_starters = []
if "last_themes" not in st.session_state:
    st.session_state.last_themes = []


def backend_healthy() -> bool:
    try:
        r = requests.get(API_BASE_URL, timeout=3)
        return r.status_code == 200
    except requests.RequestException:
        return False


# ---------------------------------------------------------------------------
# Page: Generate Starters
# ---------------------------------------------------------------------------
if page == "✨ Generate Starters":
    st.title("✨ Generate Smart Conversation Starters")
    st.write("Describe the event you're attending and what you care about — the assistant will pull out key "
             "themes and craft tailored conversation openers.")

    col1, col2 = st.columns([2, 1])
    with col1:
        event_description = st.text_area(
            "Event description",
            placeholder='e.g. "AI for Sustainable Cities" summit with panels on smart infrastructure',
            height=110,
        )
        interests_raw = st.text_input(
            "Your interests (comma-separated)",
            placeholder="climate change, urban planning",
        )
        bio = st.text_area("Short bio (optional)", placeholder="Product manager passionate about climate tech.", height=80)

    with col2:
        num_starters = st.slider("Number of starters", 1, 5, 3)
        st.info("💡 Tip: the more specific your event description, the sharper the extracted themes.")

    if st.button("Generate Starters 🚀", type="primary", use_container_width=True):
        if not event_description.strip():
            st.warning("Please enter an event description first.")
        else:
            interests = [i.strip() for i in interests_raw.split(",") if i.strip()]
            with st.spinner("Analyzing themes and generating starters..."):
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/api/v1/generate",
                        json={
                            "event_description": event_description,
                            "interests": interests,
                            "bio": bio,
                            "num_starters": num_starters,
                        },
                        timeout=120,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    st.session_state.last_interaction_id = data["interaction_id"]
                    st.session_state.last_starters = data["conversation_starters"]
                    st.session_state.last_themes = data["extracted_themes"]
                except requests.RequestException as exc:
                    st.error(f"Could not reach the backend: {exc}")

    if st.session_state.last_themes:
        st.markdown("### Extracted Themes")
        pills = "".join(f'<span class="theme-pill">{t}</span>' for t in st.session_state.last_themes)
        st.markdown(pills, unsafe_allow_html=True)

    if st.session_state.last_starters:
        st.markdown("### Your Conversation Starters")
        for i, starter in enumerate(st.session_state.last_starters, start=1):
            st.markdown(f'<div class="starter-card">💬 {starter}</div>', unsafe_allow_html=True)

        st.markdown("#### Was this helpful?")
        c1, c2, _ = st.columns([1, 1, 4])
        if c1.button("👍 Useful"):
            requests.post(f"{API_BASE_URL}/api/v1/feedback",
                          json={"interaction_id": st.session_state.last_interaction_id, "useful": True})
            st.success("Thanks for the feedback!")
        if c2.button("👎 Not useful"):
            requests.post(f"{API_BASE_URL}/api/v1/feedback",
                          json={"interaction_id": st.session_state.last_interaction_id, "useful": False})
            st.info("Thanks — we'll use this to improve future suggestions.")

# ---------------------------------------------------------------------------
# Page: Fact Check
# ---------------------------------------------------------------------------
elif page == "🔍 Fact Check":
    st.title("🔍 Quick Fact Verification")
    st.write("Look up a quick, reliable summary of a topic before you bring it up in conversation.")

    query = st.text_input("What do you want to fact-check?", placeholder="blockchain in healthcare")
    if st.button("Verify 🔎", type="primary"):
        if not query.strip():
            st.warning("Enter something to look up.")
        else:
            with st.spinner("Checking Wikipedia..."):
                try:
                    params = {"query": query}
                    if st.session_state.last_interaction_id:
                        params["interaction_id"] = st.session_state.last_interaction_id
                    resp = requests.get(f"{API_BASE_URL}/api/v1/verify", params=params, timeout=30)
                    resp.raise_for_status()
                    data = resp.json()
                except requests.RequestException as exc:
                    st.error(f"Could not reach the backend: {exc}")
                    data = None

            if data:
                if data["found"]:
                    st.markdown(
                        f'<div class="fact-box"><b>Summary:</b><br>{data["summary"]}</div>',
                        unsafe_allow_html=True,
                    )
                    if data.get("source_url"):
                        st.markdown(f"[Read more on Wikipedia]({data['source_url']})")
                else:
                    st.warning(data["summary"])

# ---------------------------------------------------------------------------
# Page: History
# ---------------------------------------------------------------------------
elif page == "🕓 History":
    st.title("🕓 Past Strategies")
    st.write("Review previously generated conversation starters and which ones you found useful.")

    if st.button("Refresh"):
        st.rerun()

    try:
        resp = requests.get(f"{API_BASE_URL}/api/v1/history", timeout=15)
        resp.raise_for_status()
        items = resp.json()["items"]
    except requests.RequestException as exc:
        st.error(f"Could not reach the backend: {exc}")
        items = []

    if not items:
        st.info("No history yet — generate some conversation starters first!")

    for item in items:
        feedback_icon = "👍" if item["feedback"] is True else ("👎" if item["feedback"] is False else "—")
        with st.expander(f"{item['event_description'][:60]}  ·  {feedback_icon}  ·  {item['created_at'][:19]}"):
            st.write("**Themes:**", ", ".join(item["extracted_themes"]) or "—")
            st.write("**Starters:**")
            for s in item["generated_starters"]:
                st.markdown(f"- {s}")
            if item["fact_check_query"]:
                st.write("**Fact check:**", item["fact_check_query"])
                st.caption(item["fact_check_result"])
