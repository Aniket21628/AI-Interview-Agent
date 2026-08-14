import uuid
from typing import Any, Optional

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from session_manager import SessionManager


fastapi_app = FastAPI(title=settings.APP_NAME, version="0.1.0")
allowed_origins = list(dict.fromkeys(settings.ALLOWED_ORIGINS + [settings.CLIENT_URL]))

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@fastapi_app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "OK",
        "message": "Interview Agent Python Server is running",
        "app": settings.APP_NAME,
        "environment": "development" if settings.DEBUG else "production",
    }


sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=allowed_origins,
    logger=settings.DEBUG,
    engineio_logger=settings.DEBUG,
)

session_manager = SessionManager()


async def emit_error(sid: str, message: str, error: Optional[str] = None) -> None:
    await sio.emit("error", {"message": message, "error": error}, room=sid)


@sio.event
async def connect(sid, environ, auth):
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    session_manager.end_session(sid)


@sio.event
async def startInterview(sid, data=None):
    data = data or {}
    candidate_profile = data.get("candidateProfile", {})
    session = session_manager.create_session(sid, candidate_profile)

    await sio.emit(
        "interviewStarted",
        {
            "sessionId": session.session_id,
            "message": session.conversation_history[-1]["message"],
            "phase": session.phase,
            "questionCount": session.question_count,
            "maxQuestions": session.max_questions,
        },
        room=sid,
    )


@sio.event
async def userMessage(sid, data=None):
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
