# components/chatbot_groq.py
import os
import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Backend API URL - can override in Streamlit secrets
if "backend_api_url" in st.secrets:
    BACKEND_URL = st.secrets["backend_api_url"]
else:
    BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

# API timeout in seconds
API_TIMEOUT = 30

# ═══════════════════════════════════════════════════════════════════════════
# MAIN CHATBOT FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def render_chatbot(role: str = "coach"):
    """
    Renders the AI chatbot using Groq API integration.
    Communicates with FastAPI backend for queries and responses.
    
    Args:
        role: 'coach' or 'player'
    """
    # Apply black background styling to chatbot section
    st.markdown("""
    <style>
        [data-testid="stTextInput"] input {
            background-color: #000000 !important;
            color: inherit !important;
        }
        .chat-container {
            background-color: #000000 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.subheader("⚡ AI Coaching Assistant" if role == "coach" else "⚡ Personal AI Coach")
    
    st.write(
        "Ask about player performance, injury risk, or get personalized recommendations."
        if role == "coach"
        else "Ask about your performance, recovery, or training adjustments."
    )
    
    # Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "backend_available" not in st.session_state:
        st.session_state.backend_available = _check_backend()
    
    # Display chat history
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    st.divider()
    
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            "Your message:",
            placeholder="Ask about player performance, injuries, or recommendations...",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("Send", use_container_width=True)
    
    # Process message
    if send_button and user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Get AI response
        if st.session_state.backend_available:
            with st.spinner("Generating response..."):
                response = _get_ai_response(user_input, role)
            
            # Add AI response to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })
        else:
            error_msg = "❌ Backend unavailable. Ensure FastAPI is running at " + BACKEND_URL
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": error_msg
            })
        
        st.rerun()
    
    # Quick suggestion buttons
    st.divider()
    st.write("**Quick questions:**")
    
    if role == "coach":
        cols = st.columns(3)
        with cols[0]:
            if st.button("Show high-risk players", use_container_width=True):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": "Show all high-risk players"
                })
                with st.spinner("Fetching..."):
                    response = _get_ai_response("Show all high-risk players", role)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })
                st.rerun()
        
        with cols[1]:
            if st.button("Team performance", use_container_width=True):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": "What is the team's overall performance status?"
                })
                with st.spinner("Fetching..."):
                    response = _get_ai_response("What is the team's overall performance status?", role)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })
                st.rerun()
        
        with cols[2]:
            if st.button("Top performers", use_container_width=True):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": "Who are the top performers this week?"
                })
                with st.spinner("Fetching..."):
                    response = _get_ai_response("Who are the top performers this week?", role)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })
                st.rerun()
    else:
        cols = st.columns(2)
        with cols[0]:
            if st.button("My performance score", use_container_width=True):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": "What's my current performance score?"
                })
                with st.spinner("Fetching..."):
                    response = _get_ai_response("What's my current performance score?", role)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })
                st.rerun()
        
        with cols[1]:
            if st.button("Recovery tips", use_container_width=True):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": "What recovery tips do you recommend for me?"
                })
                with st.spinner("Fetching..."):
                    response = _get_ai_response("What recovery tips do you recommend for me?", role)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })
                st.rerun()


def _check_backend() -> bool:
    """Check if backend API is available."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def _get_ai_response(user_message: str, role: str) -> str:
    """
    Get AI response from backend API using Groq.
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat/query-with-data",
            json={
                "message": user_message,
                "role": role
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Format response with data if available
            if data.get("data"):
                return _format_response_with_data(data["response"], data["data"])
            else:
                return data["response"]
        else:
            return f"Error: {response.text}"
    
    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return f"❌ Cannot connect to backend at {BACKEND_URL}. Make sure FastAPI is running."
    except Exception as e:
        return f"❌ Error: {str(e)}"


def _format_response_with_data(response_text: str, data: list) -> str:
    """Format AI response with data in a readable way."""
    formatted = f"{response_text}\n\n"
    
    if data:
        formatted += "**Data Retrieved:**\n"
        try:
            df = pd.DataFrame(data)
            formatted += df.to_string(index=False)
        except:
            formatted += str(data)
    
    return formatted
