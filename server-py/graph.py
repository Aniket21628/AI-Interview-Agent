from __future__ import annotations

from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

from session_manager import ANSWER_QUALITY, INTERVIEW_PHASES


class InterviewState(dict):
    def __init__(self, **kwargs):
        super().__init__()
        self["session_id"] = kwargs.get("session_id", "")
        self["current_phase"] = kwargs.get("current_phase", INTERVIEW_PHASES["INTRODUCTION"])
        self["question_count"] = kwargs.get("question_count", 0)
        self["max_questions"] = kwargs.get("max_questions", 15)
        self["last_question"] = kwargs.get("last_question", "")
        self["last_answer"] = kwargs.get("last_answer", "")
        self["last_answer_quality"] = kwargs.get("last_answer_quality", ANSWER_QUALITY["GOOD"])
        self["conversation_history"] = kwargs.get("conversation_history", [])
        self["candidate_profile"] = kwargs.get("candidate_profile", {})
        self["asked_questions"] = kwargs.get("asked_questions", [])
        self["needs_follow_up"] = kwargs.get("needs_follow_up", False)
        self["user_requested_repeat"] = kwargs.get("user_requested_repeat", False)
        self["user_requested_clarification"] = kwargs.get("user_requested_clarification", False)
        self["interview_complete"] = kwargs.get("interview_complete", False)
        self["last_evaluation"] = kwargs.get("last_evaluation", None)


async def start_interview_node(state: InterviewState) -> InterviewState:
    message = "Hello! Welcome to your interview today. I'm excited to get to know you better."
    question = "Let's start with introductions. Could you please tell me your name and a bit about yourself?"
    state["current_phase"] = INTERVIEW_PHASES["INTRODUCTION"]
    state["last_question"] = question
    state["conversation_history"] = [
        {"role": "assistant", "message": message, "timestamp": "now"},
        {"role": "assistant", "message": question, "timestamp": "now"},
    ]
    return state


async def analyze_answer_node(state: InterviewState) -> InterviewState:
    answer = (state.get("last_answer") or "").lower()
    repeat_keywords = ["repeat", "again", "say that again", "didn't catch"]
    clarify_keywords = ["confused", "unclear", "don't understand", "what do you mean", "clarify"]

    if any(keyword in answer for keyword in repeat_keywords):
        state["user_requested_repeat"] = True
        state["last_answer_quality"] = ANSWER_QUALITY["GOOD"]
        return state

    if any(keyword in answer for keyword in clarify_keywords):
        state["user_requested_clarification"] = True
        state["last_answer_quality"] = ANSWER_QUALITY["NEEDS_CLARIFICATION"]
        return state

    if len(answer) < 20:
        state["last_answer_quality"] = ANSWER_QUALITY["INSUFFICIENT"]
        state["needs_follow_up"] = True
    elif len(answer) < 50:
        state["last_answer_quality"] = ANSWER_QUALITY["NEEDS_CLARIFICATION"]
        state["needs_follow_up"] = True
    else:
        state["last_answer_quality"] = ANSWER_QUALITY["GOOD"]
        state["needs_follow_up"] = False

    state["conversation_history"].append({"role": "user", "message": state.get("last_answer", ""), "timestamp": "now"})
    return state


async def generate_follow_up_node(state: InterviewState) -> InterviewState:
    questions = {
        INTERVIEW_PHASES["INTRODUCTION"]: [
            "Could you elaborate on that a bit more?",
            "Can you give me a specific example?",
            "What aspects of that experience were most valuable to you?",
        ],
        INTERVIEW_PHASES["TECHNICAL"]: [
            "What technologies did you use in that project?",
            "What challenges did you face and how did you overcome them?",
        ],
        INTERVIEW_PHASES["BEHAVIORAL"]: [
            "How did you handle that situation?",
            "What was the outcome?",
        ],
    }
    scope = questions.get(state.get("current_phase"), questions[INTERVIEW_PHASES["INTRODUCTION"]])
    question = scope[0]
    state["last_question"] = question
    state["needs_follow_up"] = False
    state["conversation_history"].append({"role": "assistant", "message": question, "timestamp": "now"})
    return state


async def generate_next_question_node(state: InterviewState) -> InterviewState:
    if state.get("current_phase") == INTERVIEW_PHASES["INTRODUCTION"] and state.get("question_count", 0) >= 4:
        state["current_phase"] = INTERVIEW_PHASES["TECHNICAL"]
        question = "Now let's talk about your technical experience. Can you describe a challenging project you worked on recently?"
    elif state.get("current_phase") == INTERVIEW_PHASES["TECHNICAL"] and state.get("question_count", 0) >= 8:
        state["current_phase"] = INTERVIEW_PHASES["BEHAVIORAL"]
        question = "Let's talk about some behavioral scenarios. Tell me about a time when you had to work with a difficult team member."
    elif state.get("current_phase") == INTERVIEW_PHASES["BEHAVIORAL"] and state.get("question_count", 0) >= 12:
        state["current_phase"] = INTERVIEW_PHASES["CLOSING"]
        question = "We're nearing the end of our interview. Do you have any questions about the role or our company?"
    else:
        question = "What are your career goals for the next few years?"

    state["question_count"] = (state.get("question_count") or 0) + 1
    state["last_question"] = question
    state["asked_questions"] = list(state.get("asked_questions", [])) + [question]
    state["conversation_history"].append({"role": "assistant", "message": question, "timestamp": "now"})
    return state


def build_graph():
    workflow = StateGraph(InterviewState)
    workflow.add_node("startInterview", start_interview_node)
    workflow.add_node("analyzeAnswer", analyze_answer_node)
    workflow.add_node("generateFollowUp", generate_follow_up_node)
    workflow.add_node("generateNextQuestion", generate_next_question_node)

    workflow.add_edge(START, "startInterview")
    workflow.add_edge("startInterview", END)
    workflow.add_edge("analyzeAnswer", END)
    workflow.add_edge("generateFollowUp", END)
    workflow.add_edge("generateNextQuestion", END)

    return workflow.compile()
