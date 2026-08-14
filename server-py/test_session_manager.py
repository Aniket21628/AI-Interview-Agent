import random
import unittest

from session_manager import InterviewSession


class InterviewSessionTests(unittest.TestCase):
    def test_generate_next_question_uses_profile_context_when_llm_is_unavailable(self):
        random.seed(0)
        session = InterviewSession(
            "session-123",
            {
                "name": "Ava Patel",
                "position": "Senior Python Engineer",
                "experience": "6 years",
                "skills": ["Python", "FastAPI", "SQL", "Leadership"],
                "resumeSummary": "Built backend systems for fintech and led platform migration.",
            },
        )
        session._call_llm = lambda prompt: None

        question = session._generate_next_question()

        self.assertTrue(
            any(keyword.lower() in question.lower() for keyword in ["python", "fastapi", "sql", "leadership", "backend", "ava"]),
            f"Expected profile-aware fallback question, got: {question}",
        )


if __name__ == "__main__":
    unittest.main()
