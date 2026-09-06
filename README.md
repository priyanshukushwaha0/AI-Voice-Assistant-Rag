# Low-Latency AI Voice Assistant-RAG

A real-time, speech-to-speech AI voice assistant built to achieve sub-1.5 second end-to-end response latency. The system features a Streamlit frontend for microphone audio capture, a high-performance FastAPI backend, Sarvam AI for state-of-the-art Indian language STT/TTS, an embedded in-memory Qdrant instance for lightning-fast RAG context retrieval, and Groq LLM acceleration.

---

## Key Features

* **Sub-1.5s Response Time**: Optimized pipeline architecture delivering voice responses in real time.
* **Embedded In-Memory Qdrant RAG**: Runs vector search locally inside the Python runtime (`:memory:`), providing sub-150ms context retrieval without requiring Docker containers.
* **Sarvam AI Audio Stack**: High-accuracy Speech-to-Text (`saaras:v4`) and natural-sounding Text-to-Speech synthesis (`bulbul:v3`).
* **Groq Acceleration**: Ultra-fast token generation using high-throughput LLM models.
* **Zero External Container Overhead**: Uses a custom Python in-memory TTL cache to eliminate external Redis setup while retaining sub-10ms cache lookups.
* **Short-Term Context Memory**: Maintains full conversation history for the last 3 turns while keeping total prompt size under 1,000 tokens.

---

## Technologies Used

* **Frontend UI** | Streamlit
* **Backend API** | FastAPI & Uvicorn
* **Speech-to-Text (STT)** | Sarvam AI (`saaras:v4`)
* **Text-to-Speech (TTS)** | Sarvam AI (`bulbul:v3`)
* **LLM Engine** | Groq Cloud API (`openai/gpt-oss-120b`)
* **Vector Database (RAG)** | Embedded Qdrant (`:memory:`)
* **HTTP Client** | `httpx`
* **Language** | Python 3.10+

---

## Run the Deployed Application

Live Application: https://ai-voice-assistant-rag.streamlit.app/

---

## How to Run the Project Second Option

1. **Clone the repository**
   ```bash
   git clone https://github.com/priyanshukushwaha0/AI-Voice-Assistant-Rag.git
   cd AI-Voice-Assistant-Rag

2. Create a virtual environment --> python -m venv myenv

3. Create a .env file -->
   
 - GROQ_API_KEY=your_groq_api_key_here
 - SARVAM_API_KEY=your_sarvam_api_key_here
 - HF_HUB_DISABLE_SYMLINKS=1

5. Install dependencies --> pip install -r requirements.txt

6. Launch the Application -->

- Start the FastAPI Backend Server (Terminal 1) : python backend.py
- Start the Streamlit Frontend     (Terminal 2) : streamlit run frontend.py

---

## File Structure

    AI-Voice-Assistant-Rag/
            ├── .env               # API credentials (SARVAM_API_KEY, GROQ_API_KEY)
            ├── frontend.py        # Streamlit frontend for mic capture and audio playback
            ├── backend.py         # FastAPI backend server handling orchestration & execution
            ├── qdrant_rag.py      # Embedded in-memory Qdrant retriever & vector store
            ├── n8n_workflow.json  # n8n webhook orchestration export file
            ├── requirements.txt   # Python dependency list
            └── README.md          # Project documentation

---

## Usage

- Open http://localhost:8501 in your browser.

- Click 🔴 Start Recording and speak into your microphone.

- Click ⏹️ Stop Recording.

- The system will process your query and automatically play back the audio response.

---

The system will process your query and automatically play back the audio response.
##  Project Architecture

```text
[ User Mic Audio ]
        │
        ▼
[ Streamlit App (app.py) ]
        │  (POST /api/voice-process)
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (backend.py)                │
│                                                                 │
│  1. Sarvam STT (saaras:v4) ──► Transcribes Audio to Text        │
│                                                                 │
│  2. In-Memory Cache Check ───► Instant response on cache hit    │
│                                                                 │
│  3. Qdrant RAG (qdrant_rag.py) ─► Vector Context Lookup (<150ms)│
│                                                                 │
│  4. Groq LLM Generation ─────► Generates concise response       │
│                                                                 │
│  5. Sarvam TTS (bulbul:v3) ───► Synthesizes response to WAV     │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
[ Audio Response Playback ]


