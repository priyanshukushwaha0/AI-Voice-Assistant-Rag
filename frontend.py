import streamlit as st
import streamlit.components.v1 as components
import os

st.set_page_config(page_title="Low-Latency AI Voice Assistant-RAG", layout="centered")

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
    header { visibility: hidden; }
    footer { visibility: hidden; }
    .block-container { padding-top: 2rem; max-width: 750px; }
</style>
""", unsafe_allow_html=True)

# Custom HTML/JS component embedded in Streamlit for continuous voice conversation loop
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 10px;
        }}
        .header {{
            font-size: 26px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 20px;
        }}
        .status-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }}
        .status-text {{
            font-size: 15px;
            font-weight: 500;
            color: #8b949e;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .badge-latency {{
            background: #3b1719;
            color: #f87171;
            border: 1px solid #5c2427;
            padding: 5px 14px;
            border-radius: 12px;
            font-size: 13px;
            font-family: monospace;
        }}
        .control-row {{
            display: flex;
            gap: 12px;
            width: 100%;
        }}
        .btn-toggle {{
            flex: 3;
            padding: 14px;
            border-radius: 8px;
            border: 1px solid #30363d;
            background-color: #1f6feb;
            color: #ffffff;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .btn-toggle.recording {{
            background-color: #da3633;
            border-color: #f85149;
        }}
        .btn-latency-check {{
            flex: 1;
            padding: 14px;
            border-radius: 8px;
            border: 1px solid #30363d;
            background-color: #161b22;
            color: #c9d1d9;
            font-size: 14px;
            font-weight: 600;
            cursor: default;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">Low-Latency AI Voice Assistant-RAG</div>
    
    <div class="status-row">
        <div id="status-text" class="status-text">● Idle</div>
    </div>

    <div class="control-row">
        <button id="main-btn" class="btn-toggle" onclick="toggleSession()">
            🗣️ Start Talking
        </button>
        <div id="latency-check-btn" class="btn-latency-check">
            Latency Check: -- ms
        </div>
    </div>

    <script>
        let isRunning = false;
        let mediaRecorder = null;
        let audioChunks = [];
        let audioContext = null;
        let analyser = null;
        let micStream = null;
        const backendUrl = "{BACKEND_URL}";

        async function toggleSession() {{
            const btn = document.getElementById('main-btn');
            if (!isRunning) {{
                isRunning = true;
                btn.classList.add('recording');
                btn.innerText = '⏹️ Stop';
                startListeningLoop();
            }} else {{
                stopSession();
            }}
        }}

        function stopSession() {{
            isRunning = false;
            const btn = document.getElementById('main-btn');
            btn.classList.remove('recording');
            btn.innerText = '🗣️ Start Talking';
            updateStatus('● Idle');
            
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {{
                mediaRecorder.stop();
            }}
            if (micStream) {{
                micStream.getTracks().forEach(track => track.stop());
                micStream = null;
            }}
            if (audioContext) {{
                audioContext.close();
                audioContext = null;
            }}
        }}

        function updateStatus(text) {{
            document.getElementById('status-text').innerText = text;
        }}

        async function startListeningLoop() {{
            if (!isRunning) return;
            updateStatus('🎧 Listening...');
            audioChunks = [];

            try {{
                micStream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                mediaRecorder = new MediaRecorder(micStream);

                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const source = audioContext.createMediaStreamSource(micStream);
                analyser = audioContext.createAnalyser();
                analyser.fftSize = 512;
                source.connect(analyser);

                const bufferLength = analyser.frequencyBinCount;
                const dataArray = new Uint8Array(bufferLength);

                let speechDetected = false;
                let lastSpeechTime = Date.now();

                function checkSilence() {{
                    if (!isRunning || mediaRecorder.state === 'inactive') return;
                    
                    analyser.getByteFrequencyData(dataArray);
                    let sum = 0;
                    for (let i = 0; i < bufferLength; i++) {{
                        sum += dataArray[i];
                    }}
                    let average = sum / bufferLength;

                    if (average > 12) {{
                        speechDetected = true;
                        lastSpeechTime = Date.now();
                    }} else if (speechDetected && (Date.now() - lastSpeechTime > 900)) {{
                        mediaRecorder.stop();
                        return;
                    }}
                    requestAnimationFrame(checkSilence);
                }}

                mediaRecorder.ondataavailable = (e) => {{
                    if (e.data.size > 0) audioChunks.push(e.data);
                }};

                mediaRecorder.onstop = async () => {{
                    if (micStream) micStream.getTracks().forEach(t => t.stop());
                    if (audioContext) audioContext.close();

                    if (!isRunning || audioChunks.length === 0) return;

                    const audioBlob = new Blob(audioChunks, {{ type: 'audio/wav' }});
                    await processVoice(audioBlob);
                }};

                mediaRecorder.start(100);
                checkSilence();

            }} catch (err) {{
                console.error('Microphone error:', err);
                stopSession();
            }}
        }}

        async function processVoice(audioBlob) {{
            if (!isRunning) return;
            updateStatus('🧠 Thinking...');

            const formData = new FormData();
            formData.append('file', audioBlob, 'audio.wav');

            try {{
                const res = await fetch(backendUrl, {{ method: 'POST', body: formData }});
                if (!res.ok) throw new Error('API Error');

                const data = await res.json();
                
                if (data.latency_ms) {{
                    document.getElementById('latency-check-btn').innerText = `Latency Check: ${{data.latency_ms}} ms`;
                }}

                if (data.audio_b64) {{
                    playResponse(data.audio_b64);
                }} else {{
                    if (isRunning) startListeningLoop();
                }}

            }} catch (e) {{
                console.error(e);
                if (isRunning) setTimeout(startListeningLoop, 1000);
            }}
        }}

        function playResponse(b64Audio) {{
            if (!isRunning) return;
            updateStatus('🎤 Speaking...');

            const audio = new Audio('data:audio/wav;base64,' + b64Audio);
            
            audio.onended = () => {{
                if (isRunning) startListeningLoop();
            }};
            audio.onerror = () => {{
                if (isRunning) startListeningLoop();
            }};

            audio.play().catch(() => {{
                if (isRunning) startListeningLoop();
            }});
        }}
    </script>
</body>
</html>
"""

components.html(html_code, height=220)
