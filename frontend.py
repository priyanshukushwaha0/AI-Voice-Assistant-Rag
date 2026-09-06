import streamlit as st
from streamlit_mic_recorder import mic_recorder
import requests
import io

st.set_page_config(page_title="Low-Latency Voice Assistant", layout="centered")

st.title("Low-Latency AI Voice Assistant-RAG")
st.caption("Sarvam AI + Embedded Qdrant RAG + Groq Streaming")

BACKEND_URL = "http://localhost:8000/api/voice-process"

audio_data = mic_recorder(
    start_prompt="🔴 Start Recording",
    stop_prompt="⏹️ Stop Recording",
    key="recorder"
)

if audio_data is not None and "bytes" in audio_data:
    raw_audio = audio_data["bytes"]
    st.audio(raw_audio, format="audio/wav")
    
    with st.spinner("Processing speech and streaming response..."):
        try:
            files = {"file": ("input.wav", raw_audio, "audio/wav")}
            response = requests.post(BACKEND_URL, files=files, stream=True)
            
            if response.status_code == 200:
                audio_buffer = io.BytesIO()
                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        audio_buffer.write(chunk)
                
                audio_buffer.seek(0)
                st.audio(audio_buffer, format="audio/wav", autoplay=True)
                
                latency = response.headers.get("X-Response-Time", "N/A")
                st.success(f"Response delivered in {latency} seconds")
            else:
                try:
                    err_message = response.json().get("detail", response.text)
                except Exception:
                    err_message = response.text
                st.error(f"Backend Error ({response.status_code}): {err_message}")
        except Exception as e:
            st.error(f"Failed to connect to backend server: {str(e)}")