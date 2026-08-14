from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from llm import get_chat_model


INTERVIEW_PHASES = {
    "GREETING": "greeting",
    "INTRODUCTION": "introduction",
    "TECHNICAL": "technical",
    "BEHAVIORAL": "behavioral",
    "CLOSING": "closing",
}

ANSWER_QUALITY = {
    "GOOD": "good",
    "NEEDS_CLARIFICATION": "needs_clarification",
    "INSUFFICIENT": "insufficient",
}


class InterviewSession:
    def __init__(self, session_id: str, candidate_profile: Optional[Dict[str, Any]] = None):
        self.session_id = session_id
        self.candidate_profile = candidate_profile or {}
        self.max_questions = 15
        self.question_count = 0
        self.phase = INTERVIEW_PHASES["INTRODUCTION"]
        self.complete = False
        self.conversation_history: List[Dict[str, Any]] = []
        self.asked_questions: List[str] = []
        self.last_question = ""
        self.last_answer = ""
        self.last_answer_quality = ANSWER_QUALITY["GOOD"]
        self.needs_follow_up = False
        self.user_requested_repeat = False
        self.user_requested_clarification = False
        self.resume_text = str(self.candidate_profile.get("resumeText") or self.candidate_profile.get("resume") or "").strip()
        self.resume_summary = str(self.candidate_profile.get("resumeSummary") or "").strip()
        self.name = str(self.candidate_profile.get("name") or "Candidate").strip()
        self.position = str(self.candidate_profile.get("position") or "the role").strip()
        self.experience = str(self.candidate_profile.get("experience") or "").strip()
        self.skills = [str(skill).strip() for skill in self.candidate_profile.get("skills", []) if str(skill).strip()]

        self._start_with_greeting()

    def _make_message(self, role: str, message: str) -> Dict[str, Any]:
        return {
            "role": role,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _profile_context(self) -> str:
        parts = []
        if self.name and self.name.lower() != "candidate":
            parts.append(f"Candidate name: {self.name}")
        if self.position:
            parts.append(f"Target role: {self.position}")
        if self.experience:
            parts.append(f"Experience: {self.experience}")
        if self.skills:
            parts.append(f"Skills: {', '.join(self.skills[:8])}")
        if self.resume_summary:
            parts.append(f"Resume summary: {self.resume_summary}")
        if self.resume_text:
            parts.append(f"Resume context: {self.resume_text[:400]}")
        return "; ".join(parts)

    def _start_with_greeting(self) -> None:
        profile_context = self._profile_context()
        prompt = (
            "You are an interview coach. Create a warm, short interview greeting for a candidate and a first question. "
            f"Use this context: {profile_context or 'No extra resume context provided.'}. "
            "Return valid JSON with exactly two keys: 'greeting' and 'question'."
        )
        llm_reply = self._call_llm(prompt)
        if llm_reply:
            try:
                payload = json.loads(llm_reply.strip().strip("```json").strip("```"))
                greeting = str(payload.get("greeting") or "Welcome! Let's begin your interview.")
                first_question = str(payload.get("question") or "Could you tell me a bit about yourself and your background?")
            except Exception:
                greeting = "Welcome! I'm excited to learn more about you today."
                first_question = "Could you start by telling me a little about yourself and your background?"
        else:
            greeting = (
                f"Hi {self.name}! Thanks for joining me today. I'm excited to learn more about your experience for the {self.position} role."
                if self.position and self.name
                else "Hi there! Thanks for joining me today. I'm excited to learn more about you."
            )
            first_question = "Could you start by telling me a little about yourself and your background?"

        self.conversation_history.append(self._make_message("assistant", greeting))
        self.conversation_history.append(self._make_message("assistant", first_question))
        self.last_question = first_question

    def update_candidate_profile(self, profile: Dict[str, Any]) -> None:
        self.candidate_profile.update(profile)

    def _evaluate_answer(self, answer: str) -> Dict[str, Any]:
        text = answer.lower().strip()
        if not text:
            return {"quality": ANSWER_QUALITY["INSUFFICIENT"], "needs_follow_up": True}

        repeat_keywords = ["repeat", "again", "say that again", "didn't catch"]
        clarification_keywords = ["confused", "unclear", "don't understand", "what do you mean", "clarify"]

        if any(keyword in text for keyword in repeat_keywords):
            self.user_requested_repeat = True
            return {"quality": ANSWER_QUALITY["GOOD"], "needs_follow_up": False}

        if any(keyword in text for keyword in clarification_keywords):
            self.user_requested_clarification = True
            return {"quality": ANSWER_QUALITY["NEEDS_CLARIFICATION"], "needs_follow_up": True}

        if len(answer) < 20:
            return {"quality": ANSWER_QUALITY["INSUFFICIENT"], "needs_follow_up": True}
        if len(answer) < 50:
            return {"quality": ANSWER_QUALITY["NEEDS_CLARIFICATION"], "needs_follow_up": True}

        return {"quality": ANSWER_QUALITY["GOOD"], "needs_follow_up": False}

    def _call_llm(self, prompt: str) -> Optional[str]:
        try:
            llm = get_chat_model()
            response = llm.invoke(prompt)
            content = getattr(response, "content", str(response))
            if not isinstance(content, str):
                content = str(content)
            text = content.strip()
            return text or None
        except Exception:
            return None

    def _evaluate_answer_with_llm(self, answer: str) -> Dict[str, Any]:
        fallback = self._evaluate_answer(answer)
        try:
            prompt = (
                "You are evaluating a job interview candidate answer. "
                "Return only valid JSON with exactly two keys: \"quality\" and \"needs_follow_up\". "
                "Quality must be one of: good, needs_clarification, insufficient. "
                "needs_follow_up must be true or false. Candidate answer: "
                f"{answer}"
            )
            response = self._call_llm(prompt)
            if not response:
                return fallback
            parsed = json.loads(response.strip().strip("```json").strip("```"))
            quality = str(parsed.get("quality", fallback["quality"]))
            needs_follow_up = bool(parsed.get("needs_follow_up", fallback["needs_follow_up"]))
            return {"quality": quality, "needs_follow_up": needs_follow_up}
        except Exception:
            return fallback

    def _generate_follow_up(self) -> str:
        follow_up_map = {
            INTERVIEW_PHASES["INTRODUCTION"]: [
                "Could you elaborate on that a bit more?",
                "Can you give me a specific example?",
                "What aspects of that experience were most valuable to you?",
            ],
            INTERVIEW_PHASES["TECHNICAL"]: [
                "What technologies did you use in that project?",
                "What challenges did you face and how did you overcome them?",
                "What was your specific role in the project?",
            ],
            INTERVIEW_PHASES["BEHAVIORAL"]: [
                "How did you handle that situation?",
                "What was the outcome?",
                "What would you do differently next time?",
            ],
        }
        base_options = follow_up_map.get(self.phase, follow_up_map[INTERVIEW_PHASES["INTRODUCTION"]])
        prompt = (
            "You are an interview coach. Based on the candidate's previous response and current interview phase, "
            "generate exactly one short, natural follow-up interview question. "
            f"Current phase: {self.phase}. Candidate context: {self._profile_context()}. Previous answer: {self.last_answer}. "
            "Return only the question text."
        )
        llm_question = self._call_llm(prompt)
        if llm_question:
            cleaned = llm_question.strip().strip('"').strip("'")
            if cleaned:
                return cleaned
        return random.choice(base_options)

    def _fallback_question_set(self) -> Dict[str, List[str]]:
        skill_summary = ", ".join(self.skills[:4]) if self.skills else "your core technical work"
        role_context = self.position.lower() if self.position else "this role"
        experience_context = self.experience.strip() if self.experience else "your experience"
        candidate_name = self.name if self.name and self.name.lower() != "candidate" else "you"

        return {
            INTERVIEW_PHASES["INTRODUCTION"]: [
                f"Can you walk me through how your experience in {experience_context} connects to this {role_context} opportunity?",
                f"Looking at your background in {skill_summary}, what is the strongest example of impact you have delivered so far?",
                f"What part of your career so far has been most energizing, and why does it align with this role?",
                f"What motivates you to pursue a {role_context} position, and what makes you a strong fit for it?",
            ],
            INTERVIEW_PHASES["TECHNICAL"]: [
                f"Tell me about a project where you used {skill_summary} to solve a meaningful technical problem.",
                "What trade-offs did you consider when designing or scaling a solution, and how did you make the final decision?",
                "Can you describe a time you debugged a complex issue and explain how you isolated the root cause?",
                "How do you balance delivery speed with code quality or system reliability in your day-to-day work?",
            ],
            INTERVIEW_PHASES["BEHAVIORAL"]: [
                "Describe a situation where you had to influence a team or stakeholder without direct authority.",
                "Tell me about a time you had to adapt quickly when priorities changed or a project stalled.",
                "What is a challenge you faced in a team setting, and how did you help resolve it?",
                "Give me an example of feedback you received that improved your work, and what you changed as a result.",
            ],
            INTERVIEW_PHASES["CLOSING"]: [
                f"What would success look like for {candidate_name} in the first 6 months in this role?",
                "What questions do you have about the team, goals, or expectations for this position?",
                "Is there anything else you want me to know about your background that would help us evaluate fit?",
            ],
        }

    def _generate_next_question(self) -> str:
        if self.phase == INTERVIEW_PHASES["INTRODUCTION"] and self.question_count >= 4:
            self.phase = INTERVIEW_PHASES["TECHNICAL"]
            question = "Now let's talk about your technical experience. Can you describe a challenging project you worked on recently?"
        elif self.phase == INTERVIEW_PHASES["TECHNICAL"] and self.question_count >= 8:
            self.phase = INTERVIEW_PHASES["BEHAVIORAL"]
            question = "Let's talk about some behavioral scenarios. Tell me about a time when you had to work with a difficult team member."
        elif self.phase == INTERVIEW_PHASES["BEHAVIORAL"] and self.question_count >= 12:
            self.phase = INTERVIEW_PHASES["CLOSING"]
            question = "We're nearing the end of our interview. Do you have any questions about the role or our company?"
        else:
            prompt = (
                "You are a recruiter. Generate the next single best interview question for a candidate. "
                f"Current phase: {self.phase}. Candidate profile: {self._profile_context()}. "
                f"Question count: {self.question_count}. Already asked: {self.asked_questions}. "
                "Return only the question text."
            )
            llm_question = self._call_llm(prompt)
            if llm_question:
                question = llm_question.strip().strip('"').strip("'")
            else:
                fallback_questions = self._fallback_question_set()
                phase_questions = fallback_questions.get(self.phase, fallback_questions[INTERVIEW_PHASES["INTRODUCTION"]])
                available = [q for q in phase_questions if q not in self.asked_questions]
                question = random.choice(available) if available else "Thank you for your responses. Do you have any final questions for me?"

        self.asked_questions.append(question)
        return question

    def process_answer(self, answer: str) -> Dict[str, Any]:
        self.last_answer = answer
        evaluation = self._evaluate_answer_with_llm(answer)
        self.last_answer_quality = evaluation["quality"]
        self.needs_follow_up = evaluation["needs_follow_up"]

        self.conversation_history.append(self._make_message("user", answer))

        if self.user_requested_repeat:
            repeat_message = f"Let me repeat that question: {self.last_question}"
            self.conversation_history.append(self._make_message("assistant", repeat_message))
            self.user_requested_repeat = False
            return {
                "success": True,
                "message": repeat_message,
                "phase": self.phase,
                "questionCount": self.question_count,
                "maxQuestions": self.max_questions,
                "complete": self.complete,
                "evaluation": {"quality": self.last_answer_quality},
            }

        if self.user_requested_clarification:
            clarified = f"Let me ask this differently: {self.last_question} Could you tell me more about your experience with this?"
            self.conversation_history.append(self._make_message("assistant", clarified))
            self.user_requested_clarification = False
            return {
                "success": True,
                "message": clarified,
                "phase": self.phase,
                "questionCount": self.question_count,
                "maxQuestions": self.max_questions,
                "complete": self.complete,
                "evaluation": {"quality": self.last_answer_quality},
            }

        if self.needs_follow_up:
            follow_up = self._generate_follow_up()
            self.conversation_history.append(self._make_message("assistant", follow_up))
            self.last_question = follow_up
            return {
                "success": True,
                "message": follow_up,
                "phase": self.phase,
                "questionCount": self.question_count,
                "maxQuestions": self.max_questions,
                "complete": self.complete,
                "evaluation": {"quality": self.last_answer_quality},
            }

        self.question_count += 1
        if self.question_count >= self.max_questions:
            self.complete = True
            closing_message = "Thank you for your time. That concludes the interview."
            self.conversation_history.append(self._make_message("assistant", closing_message))
            self.last_question = closing_message
            return {
                "success": True,
                "message": closing_message,
                "phase": self.phase,
                "questionCount": self.question_count,
                "maxQuestions": self.max_questions,
                "complete": True,
                "evaluation": {"quality": self.last_answer_quality},
            }

        next_question = self._generate_next_question()
        self.last_question = next_question
        self.conversation_history.append(self._make_message("assistant", next_question))

        return {
            "success": True,
            "message": next_question,
            "phase": self.phase,
            "questionCount": self.question_count,
            "maxQuestions": self.max_questions,
            "complete": False,
            "evaluation": {"quality": self.last_answer_quality},
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "sessionId": self.session_id,
            "phase": self.phase,
            "questionCount": self.question_count,
            "maxQuestions": self.max_questions,
            "complete": self.complete,
            "lastQuestion": self.last_question,
        }

    def get_history(self) -> List[Dict[str, Any]]:
        return self.conversation_history


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
