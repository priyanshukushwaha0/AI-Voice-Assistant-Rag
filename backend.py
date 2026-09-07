import os, time, base64, httpx, asyncio
from collections import deque
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from huggingface_hub import AsyncInferenceClient
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Voice Assistant RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

history = deque(maxlen=2)

# Connection pool setup to keep TCP/TLS connections warm
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(10.0, connect=3.0),
    limits=httpx.Limits(max_keepalive_connections=50, max_connections=100)
)

SARVAM_KEY = os.getenv("SARVAM_API_KEY", "").strip()
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

hf_client = AsyncInferenceClient(token=HF_TOKEN if HF_TOKEN else None)
HF_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()

@app.get("/")
async def root():
    return {"status": "backend operational"}

async def transcribe(audio_bytes: bytes) -> str:
    res = await http_client.post(
        "https://api.sarvam.ai/speech-to-text",
        files={"file": ("audio.wav", audio_bytes, "audio/wav")},
        data={"model": "saaras:v4", "language_code": "en-IN", "mode": "transcribe"},
        headers={"api-subscription-key": SARVAM_KEY}
    )
    return res.json().get("transcript", "").strip() if res.status_code == 200 else ""

async def text_to_speech(text: str) -> bytes:
    payload = {
        "inputs": [text], 
        "target_language_code": "en-IN", 
        "speaker": "shubh", 
        "model": "bulbul:v3", 
        "pace": 1.3
    }
    res = await http_client.post(
        "https://api.sarvam.ai/text-to-speech",
        json=payload,
        headers={"api-subscription-key": SARVAM_KEY, "Content-Type": "application/json"}
    )
    if res.status_code == 200 and res.json().get("audios"):
        return base64.b64decode(res.json()["audios"][0])
    return b""

@app.post("/api/voice-process")
async def voice_process(file: UploadFile = File(...)):
    start_time = time.perf_counter()
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(400, "Invalid audio input")

    # Step 1: Speech-To-Text
    transcript = await transcribe(audio_bytes)
    if not transcript:
        raise HTTPException(400, "Could not transcribe audio")

    # Step 2: Ultra-Fast LLM Generation (Strict 12 token cap for speed)
    messages = [
        {"role": "system", "content": "You are a ultra-fast voice assistant. Answer directly in 1 short sentence, maximum 6 words."}
    ] + list(history) + [{"role": "user", "content": transcript}]

    try:
        completion = await hf_client.chat_completion(
            model=HF_MODEL,
            messages=messages,
            max_tokens=12,
            temperature=0.1
        )
        ai_response = completion.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(500, f"LLM Error: {e}")

    history.append({"role": "user", "content": transcript})
    history.append({"role": "assistant", "content": ai_response})

    # Step 3: Text-To-Speech Synthesis
    audio_out = await text_to_speech(ai_response)
    if not audio_out:
        raise HTTPException(500, "TTS generation failed")

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    return JSONResponse({
        "transcript": transcript,
        "ai_response": ai_response,
        "audio_b64": base64.b64encode(audio_out).decode("utf-8"),
        "latency_ms": latency_ms
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
