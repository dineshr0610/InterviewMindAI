import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine.services.interview_service import QuestionQualityEvaluator, QuestionCandidate

def test_source_competition():
    print("=== SOURCE COMPETITION VALIDATION ===")
    
    candidates = [
        QuestionCandidate(
            text="How did you implement the JWT authentication in your VibeSync project?",
            source="gemini_resume",
            category="implementation",
            topic="Authentication",
            intent="implementation",
            project="VibeSync",
            technology="JWT",
            difficulty="Medium"
        ),
        QuestionCandidate(
            text="What are the differences between session-based authentication and JWT?",
            source="supabase_bank",
            category="architecture",
            topic="Authentication",
            intent="architecture",
            project=None,
            technology="JWT",
            difficulty="Medium"
        ),
        QuestionCandidate(
            text="You mentioned using bcrypt for passwords. What salt rounds did you choose and why?",
            source="follow_up",
            category="tech_choice",
            topic="Authentication",
            intent="tech_choice",
            project=None,
            technology="bcrypt",
            difficulty="Medium"
        ),
        QuestionCandidate(
            text="How would you design an OAuth2 flow from scratch?",
            source="missing_skill",
            category="architecture",
            topic="OAuth2",
            intent="architecture",
            project=None,
            technology="OAuth2",
            difficulty="Medium"
        )
    ]
    
    # Example state
    interview_state = {
        "role": "Backend Developer",
        "recent_topics": ["Database Schema"],
        "resume_projects": ["VibeSync", "Portfolio"],
        "weak_areas": [],
        "missing_skills": ["OAuth2"]
    }
    
    print("\nEvaluating candidates...")
    for c in candidates:
        result = QuestionQualityEvaluator.evaluate(
            c,
            role_name=interview_state["role"],
            verified_technologies=["JWT", "bcrypt"],
            verified_projects=["VibeSync", "Portfolio"],
            unsupported_technologies=[],
            missing_skills=["OAuth2"],
            previous_questions=["What is your experience with databases?"],
            recent_intents=[],
            categories_covered=[],
            projects_covered=[],
            technologies_covered=[],
            last_answer="I have used PostgreSQL for most of my projects.",
            strategy="gemini_resume",
            target_difficulty="Medium",
            follow_up_depth=0,
            turn_count=2,
            total_projects=2,
            total_technologies=5
        )
        print(f"\nSource: {result.source}")
        print(f"Text: {result.text}")
        print(f"Score: {result.score:.2f}")
        print(f"Is Valid: {result.is_valid}")
        if not result.is_valid:
            print(f"Rejection Reason: {result.rejection_reason}")
        
    print("\nNote: The highest scoring candidate will be selected dynamically based on interview_state.")

if __name__ == "__main__":
    test_source_competition()
