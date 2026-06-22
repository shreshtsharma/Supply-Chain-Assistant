# front.py
import streamlit as st
import asyncio
import uuid
from agent import initialize_agent, get_agent_response

st.set_page_config(page_title="Supply Chain Risk Assistant", page_icon="🚚")
st.title("🚚 Supply Chain Risk Assistant")

if "agent" not in st.session_state:
    st.session_state.agent = None
if "config" not in st.session_state:
    st.session_state.config = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())  

if st.session_state.agent is None:
    with st.spinner("Starting Supply Chain Assistant..."):
        agent, config = asyncio.run(initialize_agent())
        config["configurable"]["thread_id"] = st.session_state.thread_id
        st.session_state.agent = agent
        st.session_state.config = config

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Ask about orders, inventory, suppliers...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = asyncio.run(get_agent_response(
                    st.session_state.agent,
                    st.session_state.config,
                    user_input
                ))
            except Exception as e:
                result = f"⚠️ Error: {str(e)[:200]}"
        st.markdown(result)

    st.session_state.messages.append({"role": "assistant", "content": result})