# Module 1 - AntiGravity Input Package

This package defines the fixed technical-role knowledge base and output contract for Module 1.

## Fixed roles
1. Frontend Developer
2. Backend Developer
3. Full Stack Developer
4. ML Engineer
5. Data Analyst
6. Data Scientist
7. DevOps Engineer
8. Cloud Engineer
9. Cybersecurity Engineer
10. Software Engineer

## Important implementation rule
The user selects exactly ONE role and uploads one PDF/DOCX resume.

Do NOT require a job description from the user.

The selected role profile acts as the reference knowledge base.

## Files
- data/technical_roles.json: role knowledge base
- data/skill_aliases.json: canonical skill normalization
- data/scoring_config.json: deterministic scoring configuration
- schemas/module1_output_schema.json: Module 1 -> Module 2 contract

## Runtime flow
Resume -> parsing -> section extraction -> technical extraction -> normalization -> role matching -> evidence extraction -> score -> feedback -> interview_context.

The interview_context is passed to Module 2 for personalized question generation.

These role definitions are the initial project dataset and should be treated as editable configuration, not hard-coded application logic.
