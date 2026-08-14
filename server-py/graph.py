import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

# pyrefly: ignore [missing-import]
from langgraph.graph import END, START, StateGraph

from llm import get_chat_model

logger = logging.getLogger("interview_agent.graph")

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

class InterviewState(TypedDict, total=False):
    session_id: str
    current_phase: str
    question_count: int
    max_questions: int
    last_question: str
    last_answer: str
    last_answer_quality: str
    needs_follow_up: bool
    user_requested_repeat: bool
    user_requested_clarification: bool
    interview_complete: bool
    candidate_profile: Dict[str, Any]
    asked_questions: List[str]
    conversation_history: List[Dict[str, Any]]
    
    # Advanced Agentic Features State
    frustration_level: int
    fact_check_failed: bool
    resume_discrepancy: bool
    discrepancy_details: str


def make_message(role: str, message: str) -> Dict[str, Any]:
    return {
        "role": role,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

def get_profile_context(profile: Dict[str, Any]) -> str:
    name = str(profile.get("name") or "Candidate").strip()
    position = str(profile.get("position") or "the role").strip()
    experience = str(profile.get("experience") or "").strip()
    skills = [str(skill).strip() for skill in profile.get("skills", []) if str(skill).strip()]
    resume_summary = str(profile.get("resumeSummary") or "").strip()
    resume_text = str(profile.get("resumeText") or profile.get("resume") or "").strip()

    parts = []
    if name and name.lower() != "candidate":
        parts.append(f"Candidate name: {name}")
    if position:
        parts.append(f"Target role: {position}")
    if experience:
        parts.append(f"Experience: {experience}")
    if skills:
        parts.append(f"Skills: {', '.join(skills[:8])}")
    if resume_summary:
        parts.append(f"Resume summary: {resume_summary}")
    if resume_text:
        parts.append(f"Resume context: {resume_text[:400]}")
    return "; ".join(parts)


def call_llm(prompt: str) -> Optional[str]:
    try:
        llm = get_chat_model()
        response = llm.invoke(prompt)
        content = getattr(response, "content", str(response))
        if not isinstance(content, str):
            content = str(content)
        return content.strip() or None
    except Exception as exc:
        logger.exception("LLM call failed: %s", exc)
        return None

def log_node(node_name: str, state: InterviewState):
    logger.info(f"==> [LangGraph] Executing Node: '{node_name}' | Session: {state.get('session_id')} | Phase: {state.get('current_phase')}")

# --- NODES ---

def start_interview_node(state: InterviewState) -> InterviewState:
    log_node("startInterview", state)
    profile_context = get_profile_context(state.get("candidate_profile", {}))
    prompt = (
        "You are an interview coach. Create a warm, short interview greeting for a candidate and a first question. "
        f"Use this context: {profile_context or 'No extra resume context provided.'}. "
        "Return valid JSON with exactly two keys: 'greeting' and 'question'."
    )
    
    llm_reply = call_llm(prompt)
    if llm_reply:
        try:
            payload = json.loads(llm_reply.strip().strip("```json").strip("```"))
            greeting = str(payload.get("greeting") or "Welcome! Let's begin your interview.")
            first_question = str(payload.get("question") or "Could you tell me a bit about yourself and your background?")
        except Exception:
            greeting = "Welcome! I'm excited to learn more about you today."
            first_question = "Could you start by telling me a little about yourself and your background?"
    else:
        name = state.get("candidate_profile", {}).get("name", "Candidate")
        greeting = f"Hi {name}! Thanks for joining me today. Let's begin."
        first_question = "Could you start by telling me a little about yourself and your background?"

    state["current_phase"] = INTERVIEW_PHASES["INTRODUCTION"]
    state["question_count"] = 1
    state["frustration_level"] = 0
    state["last_question"] = first_question
    state["conversation_history"] = state.get("conversation_history", []) + [
        make_message("assistant", greeting),
        make_message("assistant", first_question)
    ]
    return state


def analyze_answer_node(state: InterviewState) -> InterviewState:
    log_node("analyzeAnswer", state)
    answer = (state.get("last_answer") or "").strip()
    text = answer.lower()
    
    state["user_requested_repeat"] = False
    state["user_requested_clarification"] = False
    
    if not text:
        state["last_answer_quality"] = ANSWER_QUALITY["INSUFFICIENT"]
        state["needs_follow_up"] = True
        return state

    repeat_keywords = ["repeat", "again", "say that again", "didn't catch"]
    clarify_keywords = ["confused", "unclear", "don't understand", "what do you mean", "clarify"]

    if any(keyword in text for keyword in repeat_keywords):
        state["user_requested_repeat"] = True
        state["last_answer_quality"] = ANSWER_QUALITY["GOOD"]
        state["needs_follow_up"] = False
        return state

    if any(keyword in text for keyword in clarify_keywords):
        state["user_requested_clarification"] = True
        state["last_answer_quality"] = ANSWER_QUALITY["NEEDS_CLARIFICATION"]
        state["needs_follow_up"] = True
        return state

    prompt = (
        "You are evaluating a job interview candidate answer. "
        "Return only valid JSON with exactly two keys: \"quality\" and \"needs_follow_up\". "
        "Quality must be one of: good, needs_clarification, insufficient. "
        "needs_follow_up must be true or false. Candidate answer: "
        f"{answer}"
    )
    
    response = call_llm(prompt)
    if response:
        try:
            parsed = json.loads(response.strip().strip("```json").strip("```"))
            state["last_answer_quality"] = str(parsed.get("quality", ANSWER_QUALITY["GOOD"]))
            state["needs_follow_up"] = bool(parsed.get("needs_follow_up", False))
            return state
        except Exception:
            pass

    if len(answer) < 20:
        state["last_answer_quality"] = ANSWER_QUALITY["INSUFFICIENT"]
        state["needs_follow_up"] = True
    elif len(answer) < 50:
        state["last_answer_quality"] = ANSWER_QUALITY["NEEDS_CLARIFICATION"]
        state["needs_follow_up"] = True
    else:
        state["last_answer_quality"] = ANSWER_QUALITY["GOOD"]
        state["needs_follow_up"] = False

    return state


def evaluate_persona_node(state: InterviewState) -> InterviewState:
    log_node("evaluatePersona", state)
    quality = state.get("last_answer_quality")
    frust = state.get("frustration_level", 0)
    
    if quality == ANSWER_QUALITY["INSUFFICIENT"]:
        frust += 1
    elif quality == ANSWER_QUALITY["GOOD"]:
        frust = max(0, frust - 1)
        
    state["frustration_level"] = frust
    logger.info(f"==> [LangGraph] Persona adjusted. Frustration level is now {frust}")
    return state


def fact_checker_node(state: InterviewState) -> InterviewState:
    log_node("factChecker", state)
    answer = state.get("last_answer", "")
    prompt = (
        "You are a strict technical fact-checker. Determine if the candidate's technical claim in their answer is factually accurate. "
        "Return valid JSON with exactly two keys: 'accurate' (boolean) and 'reason' (string explaining the error if any). "
        f"Candidate answer: {answer}"
    )
    llm_reply = call_llm(prompt)
    state["fact_check_failed"] = False
    if llm_reply:
        try:
            payload = json.loads(llm_reply.strip().strip("```json").strip("```"))
            if not payload.get("accurate", True):
                state["fact_check_failed"] = True
                state["discrepancy_details"] = payload.get("reason", "Factually incorrect technical statement.")
        except Exception:
            pass
    return state


def confront_candidate_node(state: InterviewState) -> InterviewState:
    log_node("confrontCandidate", state)
    reason = state.get("discrepancy_details", "")
    prompt = (
        "The candidate made a factual error during a technical interview. Generate a polite but direct follow-up question confronting this error. "
        f"Error details: {reason}. Return only the question text."
    )
    question = call_llm(prompt) or "I want to push back on that slightly. Can you clarify your technical understanding there?"
    
    state["last_question"] = question
    state["conversation_history"] = state.get("conversation_history", []) + [make_message("assistant", question)]
    return state


def resume_checker_node(state: InterviewState) -> InterviewState:
    log_node("resumeChecker", state)
    answer = state.get("last_answer", "")
    resume = get_profile_context(state.get("candidate_profile", {}))
    prompt = (
        "You are verifying a candidate's claims against their resume. Check if the candidate's answer contradicts their resume context. "
        "Return valid JSON with exactly two keys: 'match' (boolean) and 'discrepancy' (string explaining the conflict if any). "
        f"Resume context: {resume}. Candidate answer: {answer}"
    )
    llm_reply = call_llm(prompt)
    state["resume_discrepancy"] = False
    if llm_reply:
        try:
            payload = json.loads(llm_reply.strip().strip("```json").strip("```"))
            if not payload.get("match", True):
                state["resume_discrepancy"] = True
                state["discrepancy_details"] = payload.get("discrepancy", "Claim doesn't match provided resume context.")
        except Exception:
            pass
    return state


def probe_discrepancy_node(state: InterviewState) -> InterviewState:
    log_node("probeDiscrepancy", state)
    reason = state.get("discrepancy_details", "")
    prompt = (
        "The candidate's answer conflicts with their resume during a behavioral interview. Generate a polite follow-up asking them to explain the discrepancy. "
        f"Discrepancy details: {reason}. Return only the question text."
    )
    question = call_llm(prompt) or "I noticed a slight discrepancy between that and your resume. Could you clarify your experience there?"
    
    state["last_question"] = question
    state["conversation_history"] = state.get("conversation_history", []) + [make_message("assistant", question)]
    return state


def generate_repeat_node(state: InterviewState) -> InterviewState:
    log_node("generateRepeat", state)
    repeat_message = f"Let me repeat that question: {state.get('last_question', '')}"
    state["conversation_history"] = state.get("conversation_history", []) + [make_message("assistant", repeat_message)]
    return state


def generate_clarification_node(state: InterviewState) -> InterviewState:
    log_node("generateClarification", state)
    clarified = f"Let me ask this differently: {state.get('last_question', '')} Could you tell me more about your experience with this?"
    state["conversation_history"] = state.get("conversation_history", []) + [make_message("assistant", clarified)]
    return state


def generate_follow_up_node(state: InterviewState) -> InterviewState:
    log_node("generateFollowUp", state)
    phase = state.get("current_phase", INTERVIEW_PHASES["INTRODUCTION"])
    profile_context = get_profile_context(state.get("candidate_profile", {}))
    last_answer = state.get("last_answer", "")
    frust = state.get("frustration_level", 0)
    persona = "warm and encouraging" if frust == 0 else ("professional" if frust == 1 else "strict and demanding")
    
    prompt = (
        f"You are a {persona} interview coach. Based on the candidate's previous response, "
        "generate exactly one short, natural follow-up interview question. "
        f"Current phase: {phase}. Candidate context: {profile_context}. Previous answer: {last_answer}. "
        "Return only the question text."
    )
    
    llm_question = call_llm(prompt)
    if llm_question:
        question = llm_question.strip().strip('"').strip("'")
    else:
        question = "Could you elaborate on that a bit more?"

    state["last_question"] = question
    state["needs_follow_up"] = False
    state["conversation_history"] = state.get("conversation_history", []) + [make_message("assistant", question)]
    return state


def generate_next_question_node(state: InterviewState) -> InterviewState:
    log_node("generateNextQuestion", state)
    state["question_count"] = state.get("question_count", 0) + 1
    count = state["question_count"]
    phase = state.get("current_phase", INTERVIEW_PHASES["INTRODUCTION"])
    frust = state.get("frustration_level", 0)
    persona = "warm and encouraging" if frust == 0 else ("professional" if frust == 1 else "strict and demanding")

    if phase == INTERVIEW_PHASES["INTRODUCTION"] and count >= 4:
        state["current_phase"] = INTERVIEW_PHASES["TECHNICAL"]
        question = "Now let's talk about your technical experience. Can you describe a challenging project you worked on recently?"
    elif phase == INTERVIEW_PHASES["TECHNICAL"] and count >= 8:
        state["current_phase"] = INTERVIEW_PHASES["BEHAVIORAL"]
        question = "Let's talk about some behavioral scenarios. Tell me about a time when you had to work with a difficult team member."
    elif phase == INTERVIEW_PHASES["BEHAVIORAL"] and count >= 12:
        state["current_phase"] = INTERVIEW_PHASES["CLOSING"]
        question = "We're nearing the end of our interview. Do you have any questions about the role or our company?"
    else:
        profile_context = get_profile_context(state.get("candidate_profile", {}))
        asked = state.get("asked_questions", [])
        prompt = (
            f"You are a {persona} recruiter. Generate the next single best interview question for a candidate. "
            f"Current phase: {phase}. Candidate profile: {profile_context}. "
            f"Question count: {count}. Already asked: {asked}. "
            "Return only the question text."
        )
        llm_question = call_llm(prompt)
        if llm_question:
            question = llm_question.strip().strip('"').strip("'")
        else:
            question = "Can you tell me more about your background?"
            
    state["last_question"] = question
    state["asked_questions"] = state.get("asked_questions", []) + [question]
    state["conversation_history"] = state.get("conversation_history", []) + [make_message("assistant", question)]
    return state


def end_interview_node(state: InterviewState) -> InterviewState:
    log_node("endInterview", state)
    state["interview_complete"] = True
    closing_message = "Thank you for your time. That concludes the interview."
    state["last_question"] = closing_message
    state["conversation_history"] = state.get("conversation_history", []) + [make_message("assistant", closing_message)]
    return state


# --- ROUTING LOGIC ---

def route_start(state: InterviewState) -> str:
    if not state.get("conversation_history"):
        return "startInterview"
    return "analyzeAnswer"


def route_after_analysis(state: InterviewState) -> str:
    return "evaluatePersona"


def route_after_persona(state: InterviewState) -> str:
    if state.get("user_requested_repeat"):
        return "generateRepeat"
    if state.get("user_requested_clarification"):
        return "generateClarification"
    if state.get("needs_follow_up"):
        return "generateFollowUp"
        
    # Check if we should trigger advanced agentic features
    phase = state.get("current_phase")
    if phase == INTERVIEW_PHASES["TECHNICAL"]:
        return "factChecker"
    elif phase == INTERVIEW_PHASES["BEHAVIORAL"]:
        return "resumeChecker"
        
    if state.get("question_count", 0) + 1 >= state.get("max_questions", 15):
        return "endInterview"
    return "generateNextQuestion"


def route_after_fact_check(state: InterviewState) -> str:
    if state.get("fact_check_failed"):
        return "confrontCandidate"
        
    if state.get("question_count", 0) + 1 >= state.get("max_questions", 15):
        return "endInterview"
    return "generateNextQuestion"


def route_after_resume_check(state: InterviewState) -> str:
    if state.get("resume_discrepancy"):
        return "probeDiscrepancy"
        
    if state.get("question_count", 0) + 1 >= state.get("max_questions", 15):
        return "endInterview"
    return "generateNextQuestion"


def build_graph():
    workflow = StateGraph(InterviewState)
    
    # Add Nodes
    workflow.add_node("startInterview", start_interview_node)
    workflow.add_node("analyzeAnswer", analyze_answer_node)
    workflow.add_node("evaluatePersona", evaluate_persona_node)
    workflow.add_node("factChecker", fact_checker_node)
    workflow.add_node("confrontCandidate", confront_candidate_node)
    workflow.add_node("resumeChecker", resume_checker_node)
    workflow.add_node("probeDiscrepancy", probe_discrepancy_node)
    workflow.add_node("generateRepeat", generate_repeat_node)
    workflow.add_node("generateClarification", generate_clarification_node)
    workflow.add_node("generateFollowUp", generate_follow_up_node)
    workflow.add_node("generateNextQuestion", generate_next_question_node)
    workflow.add_node("endInterview", end_interview_node)

    # Add Edges
    workflow.add_conditional_edges(START, route_start)
    workflow.add_edge("startInterview", END)
    
    workflow.add_edge("analyzeAnswer", "evaluatePersona")
    workflow.add_conditional_edges("evaluatePersona", route_after_persona)
    
    workflow.add_conditional_edges("factChecker", route_after_fact_check)
    workflow.add_conditional_edges("resumeChecker", route_after_resume_check)
    
    workflow.add_edge("confrontCandidate", END)
    workflow.add_edge("probeDiscrepancy", END)
    workflow.add_edge("generateRepeat", END)
    workflow.add_edge("generateClarification", END)
    workflow.add_edge("generateFollowUp", END)
    workflow.add_edge("generateNextQuestion", END)
    workflow.add_edge("endInterview", END)

    return workflow.compile()
