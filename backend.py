import os
import time
import base64
import httpx
from collections import deque
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from groq import AsyncGroq
from dotenv import load_dotenv
from qdrant_rag import KnowledgeRetriever

load_dotenv()

app = FastAPI()

# Stores last 3 conversation turns
history = deque(maxlen=6)
rag = KnowledgeRetriever()

SARVAM_KEY = os.getenv("SARVAM_API_KEY", "").strip()
GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()

async def transcribe(audio_bytes: bytes) -> str:
    """Converts input speech to text using Sarvam STT."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "https://api.sarvam.ai/speech-to-text",
                files={"file": ("audio.wav", audio_bytes, "audio/wav")},
                data={"model": "saaras:v4", "language_code": "en-IN", "mode": "transcribe"},
                headers={"api-subscription-key": SARVAM_KEY},
                timeout=10.0
            )
            if resp.status_code == 200:
                text = resp.json().get("transcript", "").strip()
                print(f"[STT User Said]: {text}")
                return text
            print(f"[STT Error {resp.status_code}]: {resp.text}")
            return ""
        except Exception as e:
            print(f"[STT Exception]: {e}")
            return ""

async def text_to_speech(text: str) -> tuple[bytes, str]:
    """Converts AI response text into WAV audio using Sarvam TTS (bulbul:v3)."""
    async with httpx.AsyncClient() as client:
        payload = {
            "inputs": [text],
            "target_language_code": "en-IN",
            "speaker": "shubh",
            "model": "bulbul:v3",
            "pace": 1.1
        }
        headers = {
            "api-subscription-key": SARVAM_KEY,
            "Content-Type": "application/json"
        }
        try:
            res = await client.post(
                "https://api.sarvam.ai/text-to-speech",
                json=payload,
                headers=headers,
                timeout=10.0
            )
            if res.status_code == 200:
                audios = res.json().get("audios", [])
                if audios:
                    return base64.b64decode(audios[0]), ""
            err_details = f"HTTP {res.status_code} - {res.text}"
            print(f"[TTS Error]: {err_details}")
            return b"", err_details
        except Exception as e:
            print(f"[TTS Exception]: {e}")
            return b"", str(e)

@app.post("/api/voice-process")
async def voice_process(file: UploadFile = File(...)):
    if not SARVAM_KEY or not GROQ_KEY or "your_" in SARVAM_KEY or "your_" in GROQ_KEY:
        raise HTTPException(status_code=401, detail="API keys missing or invalid in .env")

    start_time = time.time()
    audio_bytes = await file.read()
    if not audio_bytes or len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="Empty or invalid audio input")

    # 1. Speech-to-Text
    transcript = await transcribe(audio_bytes)
    if not transcript:
        raise HTTPException(status_code=400, detail="Could not recognize speech. Please speak again.")

    # 2. Context Retrieval (RAG)
    try:
        context = rag.retrieve_context(transcript, top_k=2)
    except Exception as e:
        print(f"[RAG Warning]: {e}")
        context = ""

    system_prompt = f"You are a helpful voice assistant. Answer concisely in 1-2 short sentences.\nContext:\n{context}"
    messages = [{"role": "system", "content": system_prompt}] + list(history) + [{"role": "user", "content": transcript}]

    # 3. Groq LLM Generation
    groq = AsyncGroq(api_key=GROQ_KEY)
    ai_response = ""

    try:
        completion = await groq.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            max_tokens=120,
            temperature=0.2
        )
        ai_response = (completion.choices[0].message.content or "").strip()
        print(f"[AI Response]: {ai_response}")
    except Exception as e:
        print(f"[Groq LLM Error]: {e}")
        raise HTTPException(status_code=500, detail=f"Groq API Error: {str(e)}")

    if not ai_response:
        raise HTTPException(status_code=500, detail="LLM returned an empty response.")

    # Save to short-term memory
    history.append({"role": "user", "content": transcript})
    history.append({"role": "assistant", "content": ai_response})

    # 4. Text-to-Speech
    audio_data, tts_err = await text_to_speech(ai_response)
    if not audio_data:
        raise HTTPException(status_code=500, detail=f"Sarvam TTS Error: {tts_err}")

    return Response(
        content=audio_data,
        media_type="audio/wav",
        headers={"X-Response-Time": str(round(time.time() - start_time, 3))}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)