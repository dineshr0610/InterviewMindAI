import re

def extract_and_normalize_question(content: str) -> dict:
    """
    Attempts to extract the core interview question from polluted markdown text.
    Returns a dictionary with:
    - classification (str)
    - normalized_question (str or None)
    - warning_flags (list of str)
    - reason (str)
    """
    if not content or not content.strip():
        return {
            "classification": "NO_QUESTION_FOUND",
            "normalized_question": None,
            "warning_flags": [],
            "reason": "Empty content"
        }
        
    content = content.strip()
    warning_flags = []
    
    # 1. Check for placeholders
    placeholder_pattern = re.compile(r'(\{technology\}|\{subject\}|\{role\}|\[insert.*?\]|<TODO>|<technology>)', re.IGNORECASE)
    if placeholder_pattern.search(content):
        warning_flags.append("PLACEHOLDER")

    # 2. Extract question text
    # Known markdown format: **Question**: ...
    # Stop patterns: **Ideal Model Answer**, **Evaluation Rubric**, **Ideal Answer**, **Model Answer**, **Scoring**, ####, etc.
    
    question_text = None
    classification = None
    reason = ""
    
    # Check if it already looks clean (no markdown headers, reasonably short)
    if not re.search(r'(\*\*Question\*\*|###|\*\*Ideal Model Answer\*\*|\*\*Evaluation Rubric\*\*)', content, re.IGNORECASE):
        words = content.split()
        q_lower = content.lower()
        is_imperative = q_lower.startswith((
            "explain", "describe", "walk me through", "compare", "discuss",
            "outline", "detail", "clarify", "elaborate", "please explain", "please describe"
        ))
        is_question = "?" in content or is_imperative
        
        if len(words) < 100 and is_question:
            classification = "ALREADY_CLEAN"
            question_text = content
            reason = "No markdown detected and looks like a valid question"
        elif len(words) >= 100:
            classification = "AMBIGUOUS"
            question_text = content
            reason = "No markdown but very long text"
        else:
            classification = "NO_QUESTION_FOUND"
            question_text = None
            reason = "No markdown and no question-like content detected"
    else:
        # Attempt extraction
        # Find "**Question**:" or "**Question**"
        q_match = re.search(r'\*\*Question\*\*[\s:]*(.*)', content, re.IGNORECASE | re.DOTALL)
        if q_match:
            raw_q = q_match.group(1)
            # Find where to stop
            stop_match = re.search(r'(\*\*Ideal.*?Answer.*?\*\*|\*\*Evaluation.*?\*\*|\*\*Model.*?Answer.*?\*\*|\*\*Scoring.*?\*\*|####)', raw_q, re.IGNORECASE)
            if stop_match:
                raw_q = raw_q[:stop_match.start()]
                
            question_text = raw_q
            classification = "VALID_EXTRACTED"
            reason = "Successfully extracted using **Question** marker"
        else:
            # Maybe it doesn't have **Question** but has ### Technical Interview Question
            if "### Technical Interview Question" in content:
                # We could try to extract everything between metadata and Ideal Answer
                pass
                
            if not question_text:
                classification = "NO_QUESTION_FOUND"
                question_text = None
                reason = "Could not identify question bounds"
                
    # If we extracted something, normalize it
    if question_text:
        # Normalize whitespace
        question_text = " ".join(question_text.strip().split())
        
        # Remove remaining markdown headers if any (e.g. ###)
        question_text = re.sub(r'#+\s*', '', question_text).strip()
        
        if len(question_text) == 0:
            classification = "NO_QUESTION_FOUND"
            question_text = None
            reason = "Question text was empty after normalization"
            
    # Classify as PLACEHOLDER if flags exist
    if "PLACEHOLDER" in warning_flags and classification in ("VALID_EXTRACTED", "ALREADY_CLEAN", "AMBIGUOUS"):
        classification = "PLACEHOLDER"
        
    return {
        "classification": classification,
        "normalized_question": question_text,
        "warning_flags": warning_flags,
        "reason": reason
    }
