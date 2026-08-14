# AI Interview Agent

A real-time, interactive AI Interview Agent designed to conduct technical and behavioral interviews. This application uses voice and text to simulate a realistic interview experience, powered by large language models (LLMs) and real-time bidirectional communication.

## 🚀 Features

- **Real-Time Voice Interaction:** Supports Speech-to-Text (Whisper API / Browser APIs) and Text-to-Speech (OpenAI TTS) for seamless conversational flow.
- **LLM-Powered Orchestration:** Built with LangChain and LangGraph to structure the interview phases and dynamically generate relevant questions based on user input.
- **Support for Leading LLMs:** Choose between **Google Gemini** or **OpenAI** as the primary language model for driving the conversation.
- **Resume Upload and Parsing:** Upload a candidate's resume (PDF). The system parses it using `PyPDF2` and tailors the interview questions dynamically based on the candidate's profile.
- **Real-Time WebSocket Communication:** Uses Socket.IO for low-latency, bidirectional communication between the Next.js frontend and the FastAPI Python backend.
- **Modern User Interface:** Built with **Next.js 14**, **Tailwind CSS**, and **Framer Motion** for a responsive, sleek, and animated user experience.

## 🛠️ Tech Stack

### Frontend (Client)
- **Framework:** Next.js 14 (React 18)
- **Styling:** Tailwind CSS, Headless UI, Framer Motion
- **Icons:** Lucide React, Heroicons
- **Communication:** Socket.IO Client

### Backend (Server)
- **Framework:** FastAPI
- **Real-Time Communication:** Python Socket.IO, Uvicorn
- **AI / LLM:** LangChain, LangGraph, OpenAI SDK, Google Generative AI
- **Document Processing:** PyPDF2 (Resume parsing)

## 📂 Project Structure

```text
interview-agent/
├── client/              # Next.js frontend application
│   ├── app/             # Next.js app router & components
│   ├── package.json     # Client dependencies
│   └── tailwind.config.js
├── server-py/           # FastAPI Python backend application
│   ├── main.py          # FastAPI application & Socket.IO events
│   ├── llm.py           # LLM logic and AI integrations
│   ├── graph.py         # LangGraph state machine definitions
│   ├── session_manager.py # WebSocket session management
│   └── requirements.txt # Python dependencies
├── .env.example         # Template for environment variables
└── DEPLOYMENT.md        # Detailed deployment guide
```

## ⚙️ Prerequisites

- **Node.js** (v18 or higher)
- **Python** (v3.10 or higher)
- API Keys for the AI services you intend to use (OpenAI API Key and/or Google Gemini API Key).

## 💻 Local Development Setup

### 1. Environment Variables

Create a `.env` file in the root directory (you can copy the provided example):

```bash
cp .env.example .env
```

Edit the `.env` file and add your configuration details and API keys.

```env
# Choose the LLM provider: "gemini" or "openai"
LLM_PROVIDER=openai

# Gemini / Google AI config
GOOGLE_API_KEY=your_google_api_key_here

# OpenAI config
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Backend Setup (FastAPI)

Navigate to the project root and set up a virtual environment for the Python backend:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1
# Mac/Linux:
# source .venv/bin/activate

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
python -m pip install -r server-py/requirements.txt

# Run the backend server
python -m uvicorn server-py.main:socket_app --host 0.0.0.0 --port 5000
```
*The backend server will run on `http://localhost:5000`.*

### 3. Frontend Setup (Next.js)

Open a new terminal window, navigate to the `client` directory, and install dependencies:

```bash
cd client

# Install dependencies
npm install

# Start the development server
npm run dev
```
*The frontend client will be available at `http://localhost:3000`.*


## 📄 License

This project is licensed under the MIT License.
