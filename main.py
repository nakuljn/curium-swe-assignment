import streamlit as st
import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

from tools import ToolService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

st.set_page_config(page_title="OpenFDA Assistant", page_icon="💊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #0d1117; }
    #MainMenu, footer, header { visibility: hidden; }
    section[data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #30363d; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] h5, section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span { color: #c9d1d9 !important; }
    section[data-testid="stSidebar"] .stButton > button {
        background: #21262d; border: 1px solid #30363d; color: #c9d1d9;
        border-radius: 6px; padding: 8px 16px; margin: 2px 0; font-size: 14px;
    }
    section[data-testid="stSidebar"] .stButton > button:hover { background: #30363d; }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #238636, #2ea043); border: none; color: #fff; font-weight: 600;
    }
    .stChatMessage { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 16px 20px; margin: 12px 0; }
    [data-testid="stChatMessageContent"] p { color: #e6edf3 !important; line-height: 1.6; font-size: 15px; }
    .stChatInput > div { background: #161b22; border: 1px solid #30363d; border-radius: 12px; }
    .stChatInput input { color: #e6edf3 !important; }
    h1, h2, h3, h4, h5 { color: #e6edf3 !important; }
    .stStatus, .stExpander { background: rgba(35,134,54,0.08); border: 1px solid rgba(35,134,54,0.3); border-radius: 8px; }
    .stExpander summary { color: #58a6ff !important; }
    hr { border-color: #30363d; }
    .welcome-box { text-align: center; padding: 60px 20px; max-width: 600px; margin: 0 auto; }
    .welcome-icon { font-size: 56px; margin-bottom: 16px; }
    .welcome-title { font-size: 26px; font-weight: 600; color: #e6edf3; margin-bottom: 8px; }
    .welcome-sub { font-size: 15px; color: #8b949e; margin-bottom: 32px; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)

if "tool_service" not in st.session_state:
    st.session_state.tool_service = ToolService()

if "conversations" not in st.session_state:
    st.session_state.conversations = {}
    st.session_state.current_conv_id = None

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("🔑 OPENAI_API_KEY not found")
    st.stop()

client = OpenAI(api_key=api_key)

INSTRUCTIONS = """You are a strictly dedicated FDA Drug Recall Assistant.
Your ONLY purpose is to query FDA recall data using the provided tools: 'search_recalls' and 'get_recall_stats'.

PROTOCOL:
1. ALWAYS check for recalls using the tools first.
2. If the user asks for medical advice (e.g., "Should I take X?", "Is X safe?"):
   - FIRST, search for recalls for that drug.
   - THEN, state if any recalls were found or not.
   - FINALLY, you MUST add this disclaimer: "I cannot provide medical advice. Please consult your healthcare provider."
3. If the user asks a general knowledge question unrelated to drugs/health (e.g., "Capital of France", "Who is the president"), reply ONLY: "No result found."
4. Do not utilize your internal knowledge base to answer general questions.

Always end your response with a source link: https://api.fda.gov/drug/enforcement.json"""

def get_tools():
    return [
        {
            "type": "function",
            "name": "search_recalls",
            "description": "Search FDA drug recalls by keyword, classification, or year",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": ["string", "null"], "description": "Search term for product name or recall reason"},
                    "classification": {"type": ["string", "null"], "enum": ["Class I", "Class II", "Class III", None], "description": "Filter by hazard class"},
                    "year": {"type": ["integer", "null"], "description": "Filter by year of recall"},
                    "limit": {"type": "integer", "description": "Max results (1-50)", "default": 10}
                },
                "required": ["query", "classification", "year", "limit"],
                "additionalProperties": False
            },
            "strict": True
        },
        {
            "type": "function",
            "name": "get_recall_stats",
            "description": "Get statistics about drug recalls (by classification, status, top firms)",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            "strict": True
        }
    ]

def run_agent(user_input, previous_response_id=None):
    tool_log = []
    
    logger.info(f"[QUERY] {user_input[:50]}...")
    
    response = client.responses.create(
        model="gpt-4o",
        instructions=INSTRUCTIONS,
        input=user_input,
        tools=get_tools(),
        previous_response_id=previous_response_id,
        store=True
    )
    
    while True:
        function_calls = [item for item in response.output if item.type == "function_call"]
        
        if not function_calls:
            break
        
        tool_outputs = []
        for fc in function_calls:
            logger.info(f"[TOOL] {fc.name}({fc.arguments})")
            result = st.session_state.tool_service.execute(fc.name, fc.arguments)
            tool_outputs.append({
                "type": "function_call_output",
                "call_id": fc.call_id,
                "output": result
            })
            tool_log.append({
                "name": fc.name,
                "args": json.loads(fc.arguments) if fc.arguments else {},
                "result": result
            })
        
        response = client.responses.create(
            model="gpt-4o",
            instructions=INSTRUCTIONS,
            input=tool_outputs,
            tools=get_tools(),
            previous_response_id=response.id,
            store=True
        )
    
    logger.info(f"[DONE] Response: {len(response.output_text or '')} chars")
    
    return response.output_text or "", response.id, tool_log

def create_new_conversation():
    conv_id = f"conv_{len(st.session_state.conversations)}"
    st.session_state.conversations[conv_id] = {
        "title": "New Chat",
        "messages": [],
        "last_response_id": None
    }
    st.session_state.current_conv_id = conv_id

with st.sidebar:
    st.markdown("### 💊 OpenFDA Assistant")
    st.caption("Responses API")
    st.divider()
    
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        create_new_conversation()
        st.rerun()
    
    st.markdown("##### Conversations")
    
    for cid, data in list(st.session_state.conversations.items())[::-1]:
        title = data["title"][:22] + "..." if len(data["title"]) > 22 else data["title"]
        is_current = cid == st.session_state.current_conv_id
        
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            if st.button(f"{'💬' if is_current else '🗨️'} {title}", key=cid, disabled=is_current, use_container_width=True):
                st.session_state.current_conv_id = cid
                st.rerun()
        with col2:
            if len(st.session_state.conversations) > 1:
                if st.button("×", key=f"del_{cid}"):
                    del st.session_state.conversations[cid]
                    if st.session_state.current_conv_id == cid:
                        st.session_state.current_conv_id = list(st.session_state.conversations.keys())[0] if st.session_state.conversations else None
                    st.rerun()

if not st.session_state.current_conv_id:
    st.markdown("""
    <div class="welcome-box">
        <div class="welcome-icon">💊</div>
        <div class="welcome-title">OpenFDA Drug Recall Assistant</div>
        <div class="welcome-sub">Built with OpenAI Responses API. Ask about FDA drug recalls.</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔍 Class I recalls", use_container_width=True):
            create_new_conversation()
            st.session_state.pending_prompt = "What are recent Class I drug recalls?"
            st.rerun()
    with col2:
        if st.button("📊 Statistics", use_container_width=True):
            create_new_conversation()
            st.session_state.pending_prompt = "Show me drug recall statistics"
            st.rerun()
    with col3:
        if st.button("🏢 Top firms", use_container_width=True):
            create_new_conversation()
            st.session_state.pending_prompt = "Which firms have the most recalls?"
            st.rerun()
    
    prompt = st.chat_input("Ask about drug recalls...")
    if prompt:
        create_new_conversation()
        st.session_state.pending_prompt = prompt
        st.rerun()
else:
    conv = st.session_state.conversations[st.session_state.current_conv_id]
    messages = conv["messages"]
    
    for msg in messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="💊"):
                if msg.get("tool_log"):
                    with st.expander("🧠 Reasoning", expanded=False):
                        for tc in msg["tool_log"]:
                            st.markdown(f"**Tool:** `{tc['name']}`")
                            st.json(tc["args"])
                            st.caption("Result:")
                            result_preview = tc["result"][:400] + "..." if len(tc["result"]) > 400 else tc["result"]
                            st.code(result_preview, language="json")
                st.markdown(msg["content"])

    pending = st.session_state.pop("pending_prompt", None)
    prompt = pending or st.chat_input("Ask about drug recalls...")

    if prompt:
        if not messages:
            st.session_state.conversations[st.session_state.current_conv_id]["title"] = " ".join(prompt.split()[:5])
        
        messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="💊"):
            placeholder = st.empty()
            
            with st.status("⚙️ Processing...", expanded=True) as status:
                try:
                    prev_id = conv.get("last_response_id")
                    response_text, new_response_id, tool_log = run_agent(prompt, prev_id)
                    
                    conv["last_response_id"] = new_response_id
                    
                    if tool_log:
                        for tc in tool_log:
                            status.write(f"📡 Called `{tc['name']}`")
                    
                    status.update(label="✅ Done", state="complete", expanded=False)
                    
                    placeholder.markdown(response_text)
                    messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "tool_log": tool_log
                    })
                    
                except Exception as e:
                    logger.error(f"Error: {e}")
                    st.error(f"🚨 Error: {e}")
        
        st.rerun()
