# Phase 2: Dataset Coverage Audit

## 1. Overall Status
- **Current Canonical Questions**: 1857
- **MVP Target per Role**: 200
- **Production Target per Role**: 500

## 2. Role Coverage

| Role | Current Count | Status |
|------|---------------|--------|
| Python Developer | 0 | RED |
| Frontend Developer | 898 | GREEN |
| Java Developer | 0 | RED |
| Database Developer | 0 | RED |
| DevOps / Cloud Engineer | 922 | GREEN |
| Backend Developer | 37 | RED |
| Data Analyst | 0 | RED |
| AI Engineer | 0 | RED |
| Machine Learning Engineer | 0 | RED |
| Full Stack Developer | 0 | RED |

## 3. Intent Coverage

The current dataset leans heavily towards conceptual explanation.

- **explain**: 1187
- **fundamentals**: 441
- **implement**: 76
- **compare**: 75
- **optimize**: 30
- **scenario**: 14
- **design**: 9
- **debug**: 8
- **architecture**: 7
- **tradeoff**: 5
- **diagnose**: 5

## 4. Gap Analysis & Quality Decisions
- **Is 1,857 enough for 10 roles?** No. Roles like Python Developer, Backend Developer, Data Analyst, etc. have ZERO valid conversational questions currently assigned to them.
- **Under-covered Roles**: Python, Java, Database, Backend, Data Analyst, AI, ML, Full Stack.
- **Under-covered Intents**: Tradeoff, architecture, design, debug, scenario.
- **Can existing Supabase records fill gaps?** Some records in `CodeAlpaca` might be adapted for coding questions, but conversational questions for missing roles must be sourced elsewhere.
- **Synthetic Question Policy**: We will reject the bad 'trade-offs' boilerplate template. High-quality generation can be used ONLY IF raw sources cannot be found.
