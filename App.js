import streamlit as st
from datetime import datetime
import json
import random
import time
import html
import os
 
# ────────────────────────────────────────────────────────────────────────────────
#   Project root structure:
#
#   project_root/
#   ├─ main.py
#   └─ assets/
#      ├─ grey.png
#      ├─ clipart.png
#      ├─ upload_image.png
#      └─ animation.json
#
#   Launch with:
#       streamlit run main.py
# ────────────────────────────────────────────────────────────────────────────────
 
# ────────────────────────────────────────────────────────────────────────────────
#  1) GLOBAL CONFIG & SESSION STATE INITIALIZATION
# ────────────────────────────────────────────────────────────────────────────────
 
st.set_page_config(
    page_title="InsightEdge",
    layout="wide",
    initial_sidebar_state="collapsed"
)
 
# Fallback helper: try to call st.experimental_rerun(); if not available, call st.stop()
def _rerun():
    try:
        st.experimental_rerun()
    except AttributeError:
        st.stop()
 
# Initialize our “router” key
if "page" not in st.session_state:
    st.session_state.page = "home"
 
# Store uploaded file objects for downstream use
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
 
# Store chat messages as a list of dicts: { role, content, timestamp }
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I am an AI assistant. How can I help you today?",
            "timestamp": datetime.now()
        }
    ]
 
# ────────────────────────────────────────────────────────────────────────────────
#  2) HELPER: Load Shared CSS
# ────────────────────────────────────────────────────────────────────────────────
 
def load_css():
    """
    Injects custom CSS so that all pages have:
      - Helvetica Neue (fallbacks: Helvetica, Arial, sans-serif)
      - Hidden Streamlit chrome (menu & footer)
      - Consistent button & container styles
      - Chat‐bubble animations / styles
      - Loading‐page typing animation
    """
    css = """
    <style>
        /* ----------------------------------------------------------------------
           Hide Streamlit menu & footer
        */
        #MainMenu, footer {
            visibility: hidden !important;
        }
 
        /* ----------------------------------------------------------------------
           Global font: Helvetica Neue (fallback: Helvetica, Arial, sans-serif)
        */
        html, body, div, h1, h2, h3, p, button, input, label {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        }
 
        /* ----------------------------------------------------------------------
           Orange CTA button style
        */
        .orange-button {
            background-color: #f97316;
            color: white;
            font-size: 1.2rem;
            font-weight: bold;
            padding: 0.8rem 2rem;
            border: none;
            border-radius: 50px;
            cursor: pointer;
        }
        .orange-button:hover {
            background-color: #ea580c;
        }
 
        /* ----------------------------------------------------------------------
           A generic “card” with semi-transparent white background
        */
        .card {
            background-color: rgba(255, 255, 255, 0.85);
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
 
        /* ----------------------------------------------------------------------
           Loading page: typing animation keyframes
        */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        .typing-box {
            font-size: 1.5rem;
            font-weight: 600;
            color: #000000;
            padding: 1rem 1.5rem;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            min-height: 70px;
            max-width: 700px;
            margin: 2rem auto;
        }
        .fade-in {
            opacity: 0;
            animation: fadeIn 1.5s ease forwards;
            animation-delay: 0.3s;
        }
 
        /* ----------------------------------------------------------------------
           Chat page styling for header, stream, bubbles
        */
        .chat-header {
            background-color: #1D4ED8;
            color: white;
            padding: 1rem;
            font-size: 1.75rem;
            text-align: center;
            border-radius: 0 0 12px 12px;
        }
        .chat-stream {
            display: flex;
            flex-direction: column;
            padding: 1rem;
            height: calc(100vh - 120px);
            overflow-y: auto;
            background: #f7f8fc;
        }
        .message {
            display: flex;
            margin-bottom: 1rem;
            align-items: flex-start;
        }
        .message.assistant { justify-content: flex-start; }
        .message.user      { justify-content: flex-end; }
        .avatar {
            font-size: 1.5rem;
            margin-right: 0.75rem;
        }
        .message.user .avatar { margin-left: 0.75rem; }
        .bubble {
            max-width: 60%;
            padding: 0.75rem 1rem;
            border-radius: 12px;
            word-wrap: break-word;
        }
        .assistant .bubble {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #e5e7eb;
            border-radius: 12px 12px 12px 0;
        }
        .user .bubble {
            background-color: #1D4ED8;
            color: #ffffff;
            border-radius: 12px 12px 0 12px;
        }
        .message-text {
            font-size: 1rem;
            line-height: 1.5;
        }
        .timestamp {
            font-size: 0.75rem;
            color: rgba(0,0,0,0.6);
            margin-top: 0.3rem;
            text-align: right;
        }
        .stChatInputContainer {
            padding: 1rem;
            background: #fafafa;
            border-top: 1px solid rgba(0,0,0,0.1);
        }
        .stChatInputContainer input {
            width: 100%;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
 
 
# ────────────────────────────────────────────────────────────────────────────────
#  3) PAGE: Home (Landing)
# ────────────────────────────────────────────────────────────────────────────────
 
def show_home():
    """
    Landing page (“Home”):
      - Title, subtitle, description
      - “Start Now” native Streamlit button (no raw HTML)
      - Right‐side illustration (clipart.png)
      - Grey background (grey.png)
      Clicking “Start Now” sets page → “upload” and triggers a rerun.
    """
    load_css()
 
    col1, col2 = st.columns([1.4, 2])
 
    with col1:
        # Card wrapper for text
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(
            """
            <h1 style='font-size:5rem; font-weight:bold; color:#1D4ED8; margin-bottom:1rem;'>
                InsightEdge
            </h1>
            <p style='font-size:1.6rem; font-weight:bold; color:#374151; margin-bottom:1rem;'>
                AI-Powered Data Insights & Report Generator
            </p>
            <p style='font-size:1.6rem; color:#6b7280; margin-bottom:1.5rem; line-height:1.6;'>
                Upload your dataset, ask any question, and get instant insights and reports powered by AI.
            </p>
            """,
            unsafe_allow_html=True
        )
 
        # Native Streamlit button for “Start Now”
        if st.button("Start Now", key="btn_start_now"):
            st.session_state.page = "upload"
            _rerun()
 
        st.markdown("</div>", unsafe_allow_html=True)
 
    with col2:
        # Display home illustration
        st.image("assets/clipart.png", use_column_width="always")
 
 
# ────────────────────────────────────────────────────────────────────────────────
#  4) PAGE: Upload Dataset
# ────────────────────────────────────────────────────────────────────────────────
 
def show_upload():
    """
    Upload page:
      - Left: illustration (upload_image.png)
      - Right: instructions + file_uploader
      - Only accepts files < 1 MB. Rejects larger files with a warning.
      - When at least one valid file exists, shows a native “Proceed” button.
      - Clicking “Proceed” stores valid files in session_state and sets page → “loading”.
    """
    load_css()
 
    col1, col2 = st.columns([2.8, 4])
 
    with col1:
        st.image("assets/upload_image.png", use_column_width="always")
 
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(
            """
            <h1 style='font-size:4rem; font-weight:bold; color:#1D4ED8; margin-bottom:1rem;'>
                Upload your dataset
            </h1>
            <p style='font-size:1.4rem; color:#6b7280; margin-bottom:1.5rem; line-height:1.6;'>
                Drag and drop your datasets or click below to upload.<br>
                Each file must be <strong>less than 1 MB</strong>.<br>
                Supported formats: <em>CSV</em>, <em>Excel</em>.
            </p>
            """,
            unsafe_allow_html=True
        )
 
        uploaded_files = st.file_uploader(
            label="Choose files (≤ 1 MB each)",
            type=["csv", "xlsx"],
            accept_multiple_files=True
        )
 
        valid_files = []
        if uploaded_files:
            for uploaded_file in uploaded_files:
                size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
                if size_mb < 1:
                    valid_files.append(uploaded_file)
                else:
                    st.warning(
                        f"File '{uploaded_file.name}' is {size_mb:.2f} MB — exceeds the 1 MB limit. It was not accepted."
                    )
 
        if valid_files:
            if st.button("Proceed with data processing", key="btn_proceed_upload"):
                # Store the actual file objects for later use
                st.session_state.uploaded_files = valid_files
                st.session_state.page = "loading"
                _rerun()
 
        st.markdown("</div>", unsafe_allow_html=True)
 
 
# ────────────────────────────────────────────────────────────────────────────────
#  5) PAGE: Loading (Interim “Waiting on API” Screen)
# ────────────────────────────────────────────────────────────────────────────────
 
def show_loading():
    """
    Loading page (no buttons):
      - Full‐screen (centered) card
      - Lottie animation (animation.json)
      - Random “facts” typed out for ~6 seconds
      - Intended to be shown while waiting on an API call
      - NO navigation button here: backend must set page → “chat” when done.
    """
    load_css()
 
    # Center the card vertically/horizontally
    st.markdown(
        "<div style='display:flex; justify-content:center; align-items:center; height:100vh;'>",
        unsafe_allow_html=True
    )
    st.markdown("<div class='card' style='max-width:800px; width:90%; text-align:center;'>", unsafe_allow_html=True)
 
    st.markdown(
        "<h2 style='font-weight:700; font-size:2rem; color:#000000; margin-bottom:1.5rem;'>"
        "Processing your data and sending it to AI..."
        "</h2>",
        unsafe_allow_html=True
    )
 
    # Load Lottie JSON
    lottie_path = os.path.join("assets", "animation.json")
    try:
        with open(lottie_path, "r") as f:
            lottie_json = json.load(f)
    except FileNotFoundError:
        st.error(f"Lottie animation not found at '{lottie_path}'.")
        lottie_json = None
 
    if lottie_json:
        from streamlit_lottie import st_lottie
        st_lottie(lottie_json, speed=1, loop=True, height=400, key="lottie_loader")
    else:
        st.warning("Unable to display loading animation.")
 
    # Show random “facts” with typing effect for ~6 seconds
    facts = [
        "📊 90% of the world’s data has been created in just the last two years.",
        "🔍 Data cleaning often consumes up to 80% of an analyst’s time.",
        "🧠 Good AI performance depends more on data quality than model size.",
        "📈 Visualizations help reveal insights that raw tables can hide.",
        "📉 Detecting outliers is key to building robust models.",
        "🛠️ Feature engineering is the heart of machine learning.",
        "📦 Data warehouses store vast amounts of historical data for analysis.",
        "📡 Streaming data enables instant insight from IoT devices.",
        "🧪 A/B testing is crucial for validating changes in products.",
        "🕵️ Data privacy is as important as data accuracy.",
        "🌐 The global data sphere is expected to reach 175 zettabytes by 2025.",
        "📚 Machine learning models can learn patterns from data without explicit programming.",
        "🔗 Data lineage tracks the flow of data through systems, ensuring transparency.",
        "📅 Time series data is essential for forecasting future trends."
    ]
    selected = random.sample(facts, 3)
    placeholder = st.empty()
    start = time.time()
    duration = 6  # seconds total
 
    while time.time() - start < duration:
        for fact in selected:
            if time.time() - start >= duration:
                break
            text_so_far = ""
            for ch in fact:
                if time.time() - start >= duration:
                    break
                text_so_far += ch
                placeholder.markdown(
                    f"<div class='typing-box fade-in'>{html.escape(text_so_far)}</div>",
                    unsafe_allow_html=True
                )
                time.sleep(0.025)
            time.sleep(0.3)
 
    st.markdown("</div></div>", unsafe_allow_html=True)
 
    # ────────────────────────────────────────────────────────────────────────────
    # NOTE:
    #   There is NO navigation button on this page. It is purely an interim screen.
    #   Once your real API call completes, you must set:
    #       st.session_state.page = "chat"
    #       _rerun()
    #   so that Streamlit re-runs and shows the Chat page.
    # ────────────────────────────────────────────────────────────────────────────
 
 
# ────────────────────────────────────────────────────────────────────────────────
#  6) PAGE: Chat Interface
# ────────────────────────────────────────────────────────────────────────────────
 
def show_chat():
    """
    Chat page:
      - Header (blue bar with “InsightEdge AI”)
      - Scrollable message stream
      - User/assistant bubbles with timestamps
      - Native st.chat_input for user text
      - Currently uses a mock AI response; replace with real API logic
    """
    load_css()
 
    # 1) Header bar
    st.markdown(
        """
        <div class="chat-header">
            🤖 InsightEdge <strong>AI</strong>
        </div>
        """,
        unsafe_allow_html=True
    )
 
    # 2) Build the scrollable chat stream
    st.markdown("<div class='chat-stream'>", unsafe_allow_html=True)
    for msg in st.session_state.messages:
        role = msg["role"]
        avatar = "🤖" if role == "assistant" else "🙂"
        # Format timestamp (Linux vs Windows)
        try:
            ts = msg["timestamp"].strftime("%-I:%M %p")
        except ValueError:
            ts = msg["timestamp"].strftime("%#I:%M %p")
        content = html.escape(msg["content"])
        bubble = (
            f"<div class='message-text'>{content}</div>"
            f"<div class='timestamp'>{ts}</div>"
        )
        st.markdown(
            f"""
            <div class="message {role}">
              <div class="avatar">{avatar}</div>
              <div class="bubble">{bubble}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)
 
    # 3) Native chat_input: on submit, append user + mock assistant reply
    user_msg = st.chat_input("Type your message here...")
    if user_msg:
        # Append user’s message
        st.session_state.messages.append({
            "role": "user",
            "content": user_msg,
            "timestamp": datetime.now()
        })
 
        # ────────────────────────────────────────────────────────────────────────
        # TODO: Replace the following mock response with your real AI/API call.
        # If you want to show the Loading page while waiting, do something like:
        #
        #   st.session_state.page = "loading"
        #   _rerun()
        #   # (When API responds, set page = "chat" & _rerun() again.)
        #
        # For now, we simply append a placeholder reply:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Thanks for your message! (This is a mock AI response.)",
            "timestamp": datetime.now()
        })
        _rerun()
 
 
# ────────────────────────────────────────────────────────────────────────────────
#  7) PAGE ROUTER
#
#   Reads st.session_state.page and dispatches accordingly.
# ────────────────────────────────────────────────────────────────────────────────
 
def main():
    if st.session_state.page == "home":
        # Home: grey background
        st.markdown(
            """
            <style>
            html, body {
                background-image: url('assets/grey.png');
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                min-height: 100vh;
                margin: 0;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        show_home()
 
    elif st.session_state.page == "upload":
        # Upload page (white/light background)
        show_upload()
 
    elif st.session_state.page == "loading":
        # Loading page (white/light background)
        show_loading()
 
    elif st.session_state.page == "chat":
        # Chat page (light background behind chat)
        st.markdown(
            """
            <style>
            html, body {
                background: #f7f8fc;
                min-height: 100vh;
                margin: 0;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        show_chat()
 
    else:
        # Unknown page → reset to home
        st.session_state.page = "home"
        _rerun()
 
 
if __name__ == "__main__":
    main()
 
