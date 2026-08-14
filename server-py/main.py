import logging
import io
# pyrefly: ignore [missing-import]
import PyPDF2
from typing import Any, Optional

# pyrefly: ignore [missing-import]
import socketio
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from config import settings
from llm import generate_speech_audio, transcribe_audio_file
from session_manager import SessionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("interview_agent.server")

fastapi_app = FastAPI(title=settings.APP_NAME, version="0.1.0")
allowed_origins = list(dict.fromkeys(settings.ALLOWED_ORIGINS + [settings.CLIENT_URL]))

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@fastapi_app.get("/health")
def health() -> dict[str, Any]:
    logger.info("Health check requested")
    return {
        "status": "OK",
        "message": "Interview Agent Python Server is running",
        "app": settings.APP_NAME,
        "environment": "development" if settings.DEBUG else "production",
    }


@fastapi_app.post("/api/voice/transcribe")
async def transcribe_voice(audio: UploadFile = File(...)) -> dict[str, Any]:
    logger.info("Voice transcription request received: filename=%s, size_bytes=%s", audio.filename, getattr(audio, "size", None))
    try:
        payload = await audio.read()
        text = transcribe_audio_file(payload, filename=audio.filename or "voice.webm")
        logger.info("Voice transcription completed: text_chars=%s", len(text.strip()))
        return {"text": text.strip()}
    except ValueError as exc:
        logger.warning("Voice transcription failed with validation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - network/provider failure path
        logger.exception("Voice transcription failed with provider error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc


@fastapi_app.post("/api/voice/speak")
async def speak_text(payload: dict[str, Any]) -> Response:
    text = str(payload.get("text", "") or "").strip()
    voice = str(payload.get("voice", "alloy") or "alloy")
    logger.info("Speech generation request received: voice=%s, text_length=%s", voice, len(text))
    if not text:
        raise HTTPException(status_code=400, detail="No text to speak")
    try:
        audio_bytes = generate_speech_audio(text, voice=voice)
        logger.info("Speech generation completed: audio_bytes=%s", len(audio_bytes))
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except ValueError as exc:
        logger.warning("Speech generation failed with validation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - provider failure path
        logger.exception("Speech generation failed with provider error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Speech generation failed: {exc}") from exc


@fastapi_app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)) -> dict[str, Any]:
    logger.info("Resume upload request received: filename=%s", file.filename)
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    try:
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        logger.info("Resume parsing completed: text_chars=%s", len(text.strip()))
        return {"text": text.strip()}
    except Exception as exc:
        logger.exception("Resume parsing failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {exc}")


sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=settings.DEBUG,
    engineio_logger=settings.DEBUG,
)

session_manager = SessionManager()


async def emit_error(sid: str, message: str, error: Optional[str] = None) -> None:
    await sio.emit("error", {"message": message, "error": error}, room=sid)


@sio.event
async def connect(sid, environ, auth):
    logger.info("Socket connected: sid=%s", sid)


@sio.event
async def disconnect(sid):
    logger.info("Socket disconnected: sid=%s", sid)
    session_manager.end_session(sid)


@sio.event
async def startInterview(sid, data=None):
    logger.info("startInterview event received: sid=%s, profile_keys=%s", sid, sorted((data or {}).get("candidateProfile", {}).keys()))
    data = data or {}
    candidate_profile = data.get("candidateProfile", {})
    session = session_manager.create_session(sid, candidate_profile)

    await sio.emit(
        "interviewStarted",
        {
            "sessionId": session.session_id,
            "message": session.get_history()[-1]["message"] if session.get_history() else "",
            "phase": session.state.get("current_phase"),
            "questionCount": session.state.get("question_count"),
            "maxQuestions": session.state.get("max_questions"),
        },
        room=sid,
    )


@sio.event
async def userMessage(sid, data=None):
    logger.info("userMessage event received: sid=%s, message_length=%s", sid, len(str((data or {}).get("message", ""))))
    data = data or {}
    message = data.get("message", "")
    session = session_manager.get_session(sid)

    if not session:
        await emit_error(sid, "No active interview session")
        return

    if not message or not str(message).strip():
        await emit_error(sid, "Message cannot be empty")
        return

    result = session.process_answer(str(message))
    if not result.get("success"):
        await emit_error(sid, "Failed to process your response", result.get("error"))
        return

    await sio.emit(
        "agentResponse",
        {
            "message": result["message"],
            "phase": result["phase"],
            "questionCount": result["questionCount"],
            "maxQuestions": result["maxQuestions"],
            "complete": result["complete"],
            "evaluation": result.get("evaluation"),
        },
        room=sid,
    )

    if result.get("complete"):
        await sio.emit(
            "interviewCompleted",
            {"sessionId": session.session_id, "conversationHistory": session.get_history()},
            room=sid,
        )


@sio.event
async def getInterviewStatus(sid):
    session = session_manager.get_session(sid)
    if not session:
        await sio.emit("interviewStatus", {"hasActiveSession": False}, room=sid)
        return

    await sio.emit("interviewStatus", {"hasActiveSession": True, **session.get_status()}, room=sid)


@sio.event
async def getConversationHistory(sid):
    session = session_manager.get_session(sid)
    history = session.get_history() if session else []
    await sio.emit("conversationHistory", {"history": history}, room=sid)


@sio.event
async def endInterview(sid):
    session = session_manager.end_session(sid)
    if not session:
        await sio.emit("interviewEnded", {"sessionId": None, "conversationHistory": []}, room=sid)
        return

    await sio.emit(
        "interviewEnded",
        {"sessionId": session.session_id, "conversationHistory": session.get_history()},
        room=sid,
    )


socket_app = socketio.ASGIApp(socketio_server=sio, other_asgi_app=fastapi_app)
