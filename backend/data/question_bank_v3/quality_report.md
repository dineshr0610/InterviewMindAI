# Phase 8C Quality Pipeline Report

## Overview
- **Source SHA-256**: `0231d302fd970db0e826ac114b820069b763f214fa541d24aba4ebc28c832f87`
- **Output SHA-256 (Canonical)**: `464e2f19567a8b2f7f74ee8cc87648922fb3b0f9a71108217f8a5e86cb0dc1fa`
- **Total Raw Records**: 5000
- **Total Canonical Valid**: 3146
- **Total Quarantined**: 1854

## Quality Issues Detected
- **Exact Duplicates**: 0
- **Prompt Leakage**: 9
- **Malformed JSON**: 0

### Quarantine Reasons Breakdown
- uncertain_role_alignment: 1846
- prompt_leakage: 9
- generic_question: 8

## Schema Discovery
Fields present in raw data:
- `primary_role`: 5000 (100.0%)
- `role`: 5000 (100.0%)
- `applicable_roles`: 5000 (100.0%)
- `primary_skill`: 5000 (100.0%)
- `secondary_skills`: 5000 (100.0%)
- `technology`: 5000 (100.0%)
- `topic`: 5000 (100.0%)
- `category`: 5000 (100.0%)
- `intent`: 5000 (100.0%)
- `difficulty`: 5000 (100.0%)
- `question_type`: 5000 (100.0%)
- `question`: 5000 (100.0%)
- `expected_answer`: 5000 (100.0%)
- `evaluation_rubric`: 5000 (100.0%)
- `id`: 5000 (100.0%)
- `source`: 4702 (94.0%)
- `provenance_type`: 4702 (94.0%)
- `dataset_version`: 4702 (94.0%)
- `status`: 4702 (94.0%)
- `ideal_answer`: 2788 (55.8%)
- `skill`: 2729 (54.6%)
- `source_url`: 1723 (34.5%)
- `source_id`: 1723 (34.5%)
- `generation_batch`: 298 (6.0%)

## Role Coverage (Valid)
- **Full Stack Developer**: 408
- **Java Developer**: 377
- **Python Developer**: 370
- **ML Engineer**: 354
- **AI Engineer**: 303
- **DevOps / Cloud Engineer**: 294
- **Database Developer**: 283
- **Backend Developer**: 280
- **Frontend Developer**: 252
- **Data Analyst**: 225

## Difficulty Distribution (Valid)
- **medium**: 1467 (46.6%)
- **hard**: 1091 (34.7%)
- **easy**: 588 (18.7%)

## Intent Distribution (Valid)
- **Assessment**: 823
- **Scenario**: 404
- **Diagnose**: 333
- **Tradeoff**: 330
- **Implement**: 294
- **Explain**: 238
- **Concept**: 179
- **Debug**: 169
- **Architecture**: 151
- **Fundamentals**: 109
- **Compare**: 69
- **Optimize**: 44
- **Design**: 3
