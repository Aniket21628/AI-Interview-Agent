import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from graph import build_graph, InterviewState, INTERVIEW_PHASES, ANSWER_QUALITY

logger = logging.getLogger("interview_agent.session")

# Compile the LangGraph workflow once to be used by all sessions
graph_app = build_graph()


class InterviewSession:
    def __init__(self, session_id: str, candidate_profile: Optional[Dict[str, Any]] = None):
        self.session_id = session_id
        
        # Initialize the LangGraph state
        self.state: InterviewState = {
            "session_id": session_id,
            "current_phase": INTERVIEW_PHASES["INTRODUCTION"],
            "question_count": 0,
            "max_questions": 15,
            "last_question": "",
            "last_answer": "",
            "last_answer_quality": ANSWER_QUALITY["GOOD"],
            "needs_follow_up": False,
            "user_requested_repeat": False,
            "user_requested_clarification": False,
            "interview_complete": False,
            "candidate_profile": candidate_profile or {},
            "asked_questions": [],
            "conversation_history": [],
            "last_llm_error_at": None
        }
        
        self._start_with_greeting()

    def _start_with_greeting(self) -> None:
        """Invokes the graph for the first time to generate the greeting and first question."""
        logger.info("Starting interview session %s via LangGraph", self.session_id)
        # Graph will route to startInterview since conversation_history is empty
        new_state = graph_app.invoke(self.state)
        self.state = new_state

    def update_candidate_profile(self, profile: Dict[str, Any]) -> None:
        self.state["candidate_profile"].update(profile)

    def process_answer(self, answer: str) -> Dict[str, Any]:
        """Processes a candidate's answer through the LangGraph state machine."""
        self.state["last_answer"] = answer
        
        # Append the user's message to history before running the graph
        self.state["conversation_history"].append({
            "role": "user",
            "message": answer,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        logger.info("Processing answer for session %s via LangGraph", self.session_id)
        # Graph will route to analyzeAnswer and then dynamically decide the next node
        new_state = graph_app.invoke(self.state)
        self.state = new_state

        # The last message in conversation_history is the agent's new response
        agent_message = ""
        if self.state["conversation_history"]:
            agent_message = self.state["conversation_history"][-1]["message"]

        return {
            "success": True,
            "message": agent_message,
            "phase": self.state["current_phase"],
            "questionCount": self.state["question_count"],
            "maxQuestions": self.state["max_questions"],
            "complete": self.state["interview_complete"],
            "evaluation": {"quality": self.state["last_answer_quality"]},
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "sessionId": self.session_id,
            "phase": self.state["current_phase"],
            "questionCount": self.state["question_count"],
            "maxQuestions": self.state["max_questions"],
            "complete": self.state["interview_complete"],
            "lastQuestion": self.state["last_question"],
        }

    def get_history(self) -> List[Dict[str, Any]]:
        return self.state.get("conversation_history", [])


class SessionManager:
    def __init__(self):
        self.active_sessions: Dict[str, InterviewSession] = {}
        self.disconnected_sessions: Dict[str, float] = {}

    def create_session(self, socket_id: str, candidate_profile: Optional[Dict[str, Any]] = None) -> InterviewSession:
        session = InterviewSession(socket_id, candidate_profile)
        self.active_sessions[socket_id] = session
        self.disconnected_sessions.pop(socket_id, None)
        return session

    def get_session(self, socket_id: str) -> Optional[InterviewSession]:
        return self.active_sessions.get(socket_id)

    def end_session(self, socket_id: str) -> Optional[InterviewSession]:
        return self.active_sessions.pop(socket_id, None)

    def mark_disconnected(self, socket_id: str) -> None:
        if socket_id in self.active_sessions:
            self.disconnected_sessions[socket_id] = datetime.now(timezone.utc).timestamp()

    def reconnect_session(self, socket_id: str) -> Optional[InterviewSession]:
        if socket_id in self.disconnected_sessions:
            self.disconnected_sessions.pop(socket_id, None)
        return self.active_sessions.get(socket_id)
