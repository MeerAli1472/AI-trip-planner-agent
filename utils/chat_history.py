import streamlit as st
import uuid


def init_session():
    """Initialize session state variables"""
    if "chats" not in st.session_state:
        st.session_state.chats = {}

    if "current_chat" not in st.session_state:
        new_chat_id = str(uuid.uuid4())
        st.session_state.current_chat = new_chat_id

        st.session_state.chats[new_chat_id] = {
            "title": "New Chat",
            "messages": []
        }


def create_new_chat():
    """Create a new chat"""
    new_chat_id = str(uuid.uuid4())
    st.session_state.current_chat = new_chat_id

    st.session_state.chats[new_chat_id] = {
        "title": "New Chat",
        "messages": []
    }


def add_message(role, content):
    """Add message to chat"""
    chat_id = st.session_state.current_chat
    chat = st.session_state.chats[chat_id]

    chat["messages"].append({
        "role": role,
        "content": content
    })

    # Set title using first user message
    if role == "user" and chat["title"] == "New Chat":
        chat["title"] = content[:40]  # limit title length


def get_messages():
    """Get messages of current chat"""
    chat_id = st.session_state.current_chat
    return st.session_state.chats[chat_id]["messages"]
