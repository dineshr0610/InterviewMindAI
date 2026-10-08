# Phase 4D - Final Master Audit

TOTAL QUESTIONS
= 2492 (Expected: 2492)

ROLE COUNTS
- Python Developer = 250 (Expected: 250)
- Frontend Developer = 250 (Expected: 250)
- Java Developer = 250 (Expected: 250)
- Database Developer = 250 (Expected: 250)
- DevOps / Cloud Engineer = 245 (Expected: 245)
- Backend Developer = 247 (Expected: 247)
- Data Analyst = 250 (Expected: 250)
- AI Engineer = 250 (Expected: 250)
- ML Engineer = 250 (Expected: 250)
- Full Stack Developer = 250 (Expected: 250)

### Integrity
- File Size: 3653191 bytes
- SHA256: 9a86edca07bc1b195de88b601345a55b45773602907c383e0ad630aff3e41092
- Malformed Lines: 0
- Missing Fields: 0
- Duplicate IDs: 0

### Duplicates & Collisions
- Exact Normalized Question Duplicates: 0
- Semantic High Similarity Pairs (>0.75): 3

### Leakage & Quality
- Leakage Flags: 6
- Short Questions (<15 chars): 0
- Short Answers (<15 chars): 0
- Median Q Length: 178.0
- Median A Length: 381.0

### Difficulties
{
  "Python Developer": {
    "easy": 34,
    "medium": 124,
    "hard": 92
  },
  "Java Developer": {
    "easy": 42,
    "medium": 127,
    "hard": 81
  },
  "DevOps / Cloud Engineer": {
    "easy": 48,
    "medium": 119,
    "hard": 78
  },
  "AI Engineer": {
    "easy": 36,
    "medium": 130,
    "hard": 84
  },
  "Database Developer": {
    "easy": 44,
    "medium": 125,
    "hard": 81
  },
  "ML Engineer": {
    "easy": 61,
    "medium": 131,
    "hard": 58
  },
  "Data Analyst": {
    "easy": 54,
    "medium": 135,
    "hard": 61
  },
  "Full Stack Developer": {
    "easy": 49,
    "medium": 133,
    "hard": 68
  },
  "Frontend Developer": {
    "easy": 44,
    "medium": 130,
    "hard": 76
  },
  "Backend Developer": {
    "easy": 47,
    "medium": 126,
    "hard": 74
  }
}

### Top Openings
- what is the: 183
- what are the: 107
- how would you: 72
- you need to: 50
- you are building: 45
- how do you: 45
- you have a: 42
- what is a: 41
- explain the concept: 37
- what tradeoffs exist: 24

### Legacy / Supabase Overlap
Could not perform exact cross-dataset duplicate check because local legacy Supabase export is not merged in this isolated script context. Prior generation phases validated locally against existing exports.

### Final Readiness Decision
**READY WITH FIXES**
Reasons: Prompt leakage flagged in 6 records
