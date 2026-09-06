import streamlit as st
from streamlit_mic_recorder import mic_recorder
import requests
import base64
import os

st.set_page_config(page_title="Low-Latency AI Voice Assistant-RAG", layout="centered")

# Production Backend Endpoint on Render
DEFAULT_BACKEND = "https://ai-voice-assistant-rag.onrender.com/api/voice-process"
RAW_URL = st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", DEFAULT_BACKEND))

# Ensure correct URL endpoint path
if not RAW_URL.endswith("/api/voice-process"):
    BACKEND_URL = RAW_URL.rstrip("/") + "/api/voice-process"
else:
    BACKEND_URL = RAW_URL

# Clean Dark Theme CSS
st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .header { font-size: 24px; font-weight: 700; color: #ffffff; margin-bottom: 8px; }
    .badge { background: #3b1719; color: #f87171; border: 1px solid #5c2427; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-family: monospace; }
    .chat-box { background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 18px; margin-top: 15px; }
    .user-lbl { color: #58a6ff; font-weight: 600; font-size: 14px; margin-top: 10px; }
    .ast-lbl { color: #3fb950; font-weight: 600; font-size: 14px; margin-top: 10px; }
    .msg-txt { color: #f0f6fc; margin-bottom: 8px; font-size: 15px; }
</style>
""", unsafe_allow_html=True)

if "chat" not in st.session_state: st.session_state.chat = []
if "latency" not in st.session_state: st.session_state.latency = None
if "last_audio" not in st.session_state: st.session_state.last_audio = None

st.markdown('<div class="header">Low-Latency AI Voice Assistant-RAG</div>', unsafe_allow_html=True)

# Header Status Row
c1, c2 = st.columns([1, 1])
with c1:
    st.markdown("<span style='color:#8b949e; font-size: 14px;'>● Idle</span>", unsafe_allow_html=True)
with c2:
    lat_str = f"first audio: {st.session_state.latency} ms" if st.session_state.latency is not None else "first audio: -- ms"
    st.markdown(f"<div style='text-align:right;'><span class='badge'>{lat_str}</span></div>", unsafe_allow_html=True)

st.write("")

# Controls
b1, b2 = st.columns([3, 1])
with b1:
    audio = mic_recorder(start_prompt="🔴 Start Recording", stop_prompt="⏹️ Stop Recording", key="recorder", use_container_width=True)
with b2:
    repeat_clicked = st.button("Repeat", use_container_width=True)

if repeat_clicked:
    if st.session_state.last_audio:
        st.audio(st.session_state.last_audio, format="audio/wav", autoplay=True)
    else:
        st.toast("No previous response audio to play.")

# Process Recorded Audio
if audio and "bytes" in audio and len(audio["bytes"]) > 0:
    with st.spinner("Processing..."):
        try:
            res = requests.post(BACKEND_URL, files={"file": ("audio.wav", audio["bytes"], "audio/wav")}, timeout=30)
            if res.status_code == 200:
                data = res.json()
                st.session_state.latency = data.get("latency_ms", "N/A")
                st.session_state.chat.extend([
                    {"role": "You", "text": data.get("transcript", "")},
                    {"role": "Assistant", "text": data.get("ai_response", "")}
                ])
                if data.get("audio_b64"):
                    audio_bytes = base64.b64decode(data["audio_b64"])
                    st.session_state.last_audio = audio_bytes
                    st.audio(audio_bytes, format="audio/wav", autoplay=True)
            else:
                st.error(res.json().get("detail", f"Error {res.status_code} from backend."))
        except Exception as e:
            st.error(f"Backend connection failed: {e}")

# Render Transcript
chat_html = '<div class="chat-box">'
if not st.session_state.chat:
    chat_html += "<span style='color:#484f58; font-style: italic;'>No conversation yet. Click 'Start Recording' to begin.</span>"
else:
    for msg in st.session_state.chat:
        cls = "user-lbl" if msg["role"] == "You" else "ast-lbl"
        chat_html += f'<div class="{cls}">{msg["role"]}</div><div class="msg-txt">{msg["text"]}</div>'
chat_html += '</div>'

st.markdown(chat_html, unsafe_allow_html=True)
