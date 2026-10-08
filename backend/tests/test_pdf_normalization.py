import pytest
from app.utils.resume import clean_resume_text

def test_pdf_normalization():
    # TEST A: Icon artifacts
    assert clean_resume_text("♂laptop-codePersonal Portfolio + AI Assistant") == "Personal Portfolio + AI Assistant"
    assert clean_resume_text("♂¶usicVibeSync — Full-Stack") == "VibeSync — Full-Stack"
    assert clean_resume_text("/envel⌢pedinesh@example.com") == "dinesh@example.com"
    
    # TEST B: URL duplicates
    assert clean_resume_text("githubgithub.com/dinesh") == "github.com/dinesh"
    assert clean_resume_text("linkedinlinkedin.com/in/dinesh") == "linkedin.com/in/dinesh"
    
    # TEST C: Concatenation
    assert clean_resume_text("(Nuxt + RAG)Ongoing Major Project") == "(Nuxt + RAG) — Ongoing Major Project"
    
    # TEST D: Preservation
    preserved = ["Nuxt", "Vue", "Node.js", "Tailwind", "RAG", "Python", "MongoDB", "Flask", "Supabase", "OpenAI API", "REST APIs", "C++", "C#", ".NET"]
    for p in preserved:
        assert p in clean_resume_text(f"Used {p} for backend")

    # TEST E: Legitimate words are not corrupted
    assert clean_resume_text("I love Music and envelope processing.") == "I love Music and envelope processing."
    assert clean_resume_text("My laptop-code is fast.") == "My laptop-code is fast."

from app.utils.resume import normalize_generated_question

def test_normalize_generated_question():
    questions = [
        "What is the time complexity of QuickSort?",
        "Can you describe how Music recommendation works?",
        "How do you process an envelope payload?",
        "Have you used laptop-code in production?",
        "Explain the difference between F ull-Stack and frontend.",
        "What does /heartbeat endpoint do?",
        "Can you \x00 explain this?",
        "   Why use    Redis?   ",
        "How would you\n\n\n\ndescribe a closure?",
        "Are there any edge cases with \u2640usic?",
    ]
    
    expected = [
        "What is the time complexity of QuickSort?",
        "Can you describe how Music recommendation works?",
        "How do you process an envelope payload?",
        "Have you used laptop-code in production?",
        "Explain the difference between F ull-Stack and frontend.",
        "What does /heartbeat endpoint do?",
        "Can you explain this?",
        "Why use Redis?",
        "How would you\n\ndescribe a closure?",
        "Are there any edge cases with \u2640usic?",
    ]
    
    for q, e in zip(questions, expected):
        assert normalize_generated_question(q) == e
