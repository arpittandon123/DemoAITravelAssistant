import streamlit as st
import asyncio
import sys
import os

from agent import TravelAssistantAgent

st.set_page_config(
    page_title="AI Travel Planning Assistant", 
    page_icon="✈️", 
    layout="wide"
)

st.title("✈️ AI Travel Assistant (Singapore)")
st.caption("Context-Aware Travel Assistant with ChromaDB RAG + Real-time MCP Tools")

# Initialize Chat Memory in Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Instantiate Singleton Agent Instance
@st.cache_resource
def get_agent():
    return TravelAssistantAgent()

try:
    agent = get_agent()
except Exception as e:
    st.error(f"Failed to initialize knowledge base: {e}")
    st.info("Make sure you have ingested documents by running: `python ingest.py`")
    st.stop()

# Sidebar: Control Panel & Status
with st.sidebar:
    st.header("⚙️ Assistant Status")
    st.success("Vector DB: ChromaDB Loaded")
    st.success("Embeddings: HuggingFace (all-MiniLM-L6-v2)")
    st.success("MCP Tool 1: Live Open-Meteo Weather")
    st.success("MCP Tool 2: Live Exchange Rate API")
    
    if st.button("Clear Chat History", type="secondary"):
        st.session_state.messages = []
        st.rerun()

# Display Conversation History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Prompt Input Box
if prompt := st.chat_input("Ask about Singapore itineraries..."):
    # Display user query in chat UI
    st.chat_message("user").markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Searching Knowledge Base & Consulting MCP Services..."):
            # Set up event loop for asynchronous MCP/LLM calls inside Streamlit
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            result = loop.run_until_complete(agent.run_query(prompt, st.session_state.messages))
            
            # Render final answer
            st.markdown(result["answer"])
            
            # Expandable Debug Panels for Evaluation & Inspection
            with st.expander("🔍 ChromaDB Retrieved Knowledge Base Context"):
                st.text(result["rag_context"])
            with st.expander("⚡ Real-time MCP Tool Execution Payload"):
                st.text(result["mcp_output"])

    # Persist message history
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})