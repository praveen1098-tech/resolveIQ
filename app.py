import streamlit as st
from agent import triage_incident
from memory_store import retain_incident

st.set_page_config(page_title="ResolveIQ - Incident Memory Agent", layout="wide", page_icon="🚨")

st.title("🚨 ResolveIQ: AI Incident Response & Root-Cause Memory Agent")
st.caption("Autonomous SRE agent powered by Hindsight persistent memory.")

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("1. Active Incident Investigation")
    service = st.selectbox(
        "Affected Microservice", 
        ["auth-service", "payment-api", "checkout-service", "notification-worker"]
    )
    error_input = st.text_area(
        "Incident Symptoms / Error Logs", 
        value="HTTP 503 Service Unavailable immediately after deployment v2.5.0",
        height=100
    )
    
    if st.button("🔎 Investigate Incident", type="primary"):
        with st.spinner("Analyzing logs & querying Hindsight memory..."):
            diagnosis, memories = triage_incident(service, error_input)
            st.session_state["diagnosis"] = diagnosis
            st.session_state["memories"] = memories

    if "diagnosis" in st.session_state:
        st.markdown("### 🤖 Agent Diagnosis & Strategy")
        st.markdown(st.session_state["diagnosis"])

with col2:
    st.subheader("2. 🧠 Hindsight Memory Inspector")
    st.caption("Real-time persistent knowledge retrieved for this incident.")
    
    if "memories" in st.session_state and st.session_state["memories"]:
        for idx, mem in enumerate(st.session_state["memories"]):
            content = mem.get("content") or mem.get("text") or str(mem)
            st.success(f"**Memory Match #{idx+1}**\n\n{content}")
    else:
        st.write("No historical memories retrieved yet. Click 'Investigate Incident' to search.")

    st.divider()

    st.subheader("3. 🔄 Close Incident & Teach Agent")
    st.caption("Store verified outcome so the agent learns for future outages.")
    
    root_cause_input = st.text_input("Verified Root Cause", placeholder="e.g., Missing JWT_SECRET in production ConfigMap")
    resolution_input = st.text_input("Resolution Applied", placeholder="e.g., Patched Kubernetes secret and restarted deployment")

    if st.button("💾 Store Resolution into Hindsight"):
        if root_cause_input and resolution_input:
            retain_incident(service, error_input, root_cause_input, resolution_input)
            st.success("✅ Knowledge saved to Hindsight! The agent will use this fix in future incidents.")
        else:
            st.error("Please provide both root cause and resolution before saving.")
