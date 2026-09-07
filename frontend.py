import streamlit as st
from streamlit_mic_recorder import mic_recorder
import requests
import base64
import os

st.set_page_config(page_title="Low-Latency AI Voice Assistant", layout="centered")

DEFAULT_BACKEND = "https://ai-voice-assistant-rag.onrender.com/api/voice-process"

try:
    RAW_URL = st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", DEFAULT_BACKEND))
except Exception:
    RAW_URL = os.getenv("BACKEND_URL", DEFAULT_BACKEND)

if not RAW_URL.endswith("/api/voice-process"):
    BACKEND_URL = RAW_URL.rstrip("/") + "/api/voice-process"
else:
    BACKEND_URL = RAW_URL

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .header { font-size: 24px; font-weight: 700; color: #ffffff; margin-bottom: 12px; text-align: center; }
    .badge { background: #1f6feb22; color: #58a6ff; border: 1px solid #1f6feb; padding: 6px 14px; border-radius: 12px; font-size: 13px; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

if "latency" not in st.session_state:
    st.session_state.latency = None

st.markdown('<div class="header">Low-Latency AI Voice Assistant</div>', unsafe_allow_html=True)

lat_str = f"Latency: {st.session_state.latency} ms" if st.session_state.latency is not None else "Latency: -- ms"
st.markdown(f"<div style='text-align:center; margin-bottom: 25px;'><span class='badge'>{lat_str}</span></div>", unsafe_allow_html=True)

audio = mic_recorder(
    start_prompt="🔴 Start Recording",
    stop_prompt="⏹️ Stop Recording",
    key="recorder",
    use_container_width=True
)

if audio and "bytes" in audio and len(audio["bytes"]) > 0:
    with st.spinner("Processing..."):
        try:
            res = requests.post(
                BACKEND_URL, 
                files={"file": ("audio.wav", audio["bytes"], "audio/wav")}, 
                timeout=60
            )
            if res.status_code == 200:
                data = res.json()
                st.session_state.latency = data.get("latency_ms", "N/A")
                if data.get("audio_b64"):
                    audio_bytes = base64.b64decode(data["audio_b64"])
                    st.audio(audio_bytes, format="audio/wav", autoplay=True)
            else:
                st.error(f"Error {res.status_code} from backend.")
        except Exception as e:
            st.error(f"Backend connection failed: {e}")
