# Low-Latency AI Voice Assistant-RAG

Low-Latency AI Voice Assistant is a real-time, low-latency conversational AI application built to deliver continuous, hands-free voice interactions. Powered by a high-performance **FastAPI** backend and an interactive **Streamlit** frontend, this system integrates Speech-to-Text (STT), Large Language Model (LLM) inference, and Text-to-Speech (TTS) pipelines to achieve sub-second voice response speeds.

---

## Key Features

* **Continuous Conversation Loop:** Automatically switches between listening, processing, and speaking without requiring manual clicks after each interaction.
* **Low-Latency Architecture:** Optimized connection pooling and strict response budgeting ensure ultra-fast end-to-end processing.
* **Real-Time Latency Tracking:** Displays live performance metrics (`Latency Check: XX ms`) for every conversational turn.
* **Minimalist UI:** Clean, distraction-free dark interface focused entirely on voice input and audio response.
* **Silence Detection:** Client-side Voice Activity Detection (VAD) automatically triggers speech processing upon user silence.

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


