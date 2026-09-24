"""
Optional lightweight dev/demo UI (spec §32).

This is retained as a fast local way to exercise the AI pipeline WITHOUT the
React frontend or auth — useful for developers and demos. It calls the same
service layer the API uses (single source of truth), so it can never drift from
production behaviour. It is NOT a second production frontend; the React SPA is
the real product UI. Run with:  streamlit run streamlit_app.py
"""

import uuid

import streamlit as st

from app.agents.interview_agent import persona_reply
from app.graph.graph import run_pipeline

st.set_page_config(page_title="Synthetic User Research (dev UI)", layout="wide")
st.title("Synthetic User Research Platform — dev UI")
st.caption("Developer/demo interface. Personas and responses are AI-generated (synthetic).")

with st.form("research_form"):
    product = st.text_area("Product description", height=90)
    audience = st.text_area("Target audience", height=70)
    goal = st.text_area("Research goal", height=70)
    c1, c2 = st.columns(2)
    num_personas = c1.slider("Personas", 2, 10, 4)
    num_questions = c2.slider("Survey questions", 3, 12, 6)
    submitted = st.form_submit_button("Run pipeline")

if submitted:
    if not (product and audience and goal):
        st.error("Product, audience and research goal are required.")
    else:
        with st.spinner("Running persona → survey → response → insight pipeline..."):
            state = run_pipeline(
                product,
                audience,
                goal,
                num_personas,
                num_questions,
                run_id=f"dev-{uuid.uuid4().hex[:8]}",
            )
        st.session_state["state"] = state
        st.session_state["product"] = product
        st.session_state["chats"] = {}

state = st.session_state.get("state")
if state:
    st.header("Generated Personas (synthetic)")
    cols = st.columns(2)
    for i, p in enumerate(state["personas"]):
        with cols[i % 2].container(border=True):
            st.subheader(p.name)
            st.caption(f"{p.age} — {p.occupation} · tech-savviness: {p.tech_savviness}")
            st.markdown(f"**Goals:** {', '.join(p.goals)}")
            st.markdown(f"**Pain points:** {', '.join(p.pain_points)}")
            st.markdown(f"_{p.persona_summary}_")

    report = state["insight_report"]
    st.header("Insights")
    st.info(report.executive_summary)
    st.markdown("**Recommendations:**")
    for r in report.recommendations:
        st.markdown(f"- {r}")

    st.header("Chat with a persona")
    names = [p.name for p in state["personas"]]
    sel = st.selectbox("Persona", names)
    persona = next(p for p in state["personas"] if p.name == sel)
    chats = st.session_state.setdefault("chats", {})
    history = chats.setdefault(persona.id, [])
    for role, content in history:
        st.chat_message("user" if role == "user" else "assistant").write(content)
    msg = st.chat_input(f"Ask {persona.name} something...")
    if msg:
        st.chat_message("user").write(msg)
        pd = {**persona.model_dump()}
        reply = persona_reply(
            pd, history, msg, product_description=st.session_state.get("product", "")
        )
        st.chat_message("assistant").write(reply)
        history.append(("user", msg))
        history.append(("persona", reply))
