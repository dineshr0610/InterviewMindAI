import json
import os
import sys

def build_full_audit_json():
    # Load intermediate raw files
    raw_path = "reports/database_dataset_forensic_audit_raw.json"
    deep_path = "reports/deep_metadata_audit.json"
    defects_path = "reports/question_quality_defects_samples.json"
    dups_path = "reports/duplicates_analysis.json"
    manifest_path = "reports/question_bank_cleanup_migration.json"
    
    with open(raw_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    with open(deep_path, "r", encoding="utf-8") as f:
        deep_data = json.load(f)
    with open(defects_path, "r", encoding="utf-8") as f:
        defects_data = json.load(f)
    with open(dups_path, "r", encoding="utf-8") as f:
        dups_data = json.load(f)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
        
    audit_json = {
        "audit_metadata": {
            "version": "1.0.0",
            "audit_type": "Phase 0 Complete Database + Dataset Forensic Audit",
            "target": "Supabase PostgreSQL & InterviewMind AI Dataset",
            "scope": [
                "Part 1: Database Schema Inventory",
                "Part 2: Relationship Map",
                "Part 3: document_embeddings Forensic Audit",
                "Part 4: Actual Dataset Schema",
                "Part 5: Skill Analysis",
                "Part 6: Question Quality Analysis",
                "Part 7: Difficulty Analysis",
                "Part 8: Role Analysis",
                "Part 9: Category / Intent / Strategy Analysis",
                "Part 10: Embedding Audit",
                "Part 11: Duplicate Analysis",
                "Part 12: Other Tables Audit",
                "Part 13: Application <-> Database Mapping",
                "Part 14: Ideal Dataset Contract",
                "Part 15: Dataset Problems vs Code Problems",
                "Part 16: Final Recommendation"
            ],
            "execution_mode": "READ-ONLY",
            "gemini_api_calls_made": 0
        },
        "part_1_schema_inventory": raw_data["schema_inventory"],
        "part_1_rpcs": raw_data["rpcs"],
        "part_2_relationship_map": {
            "foreign_key_relationships": [
                {
                    "source_table": "interview_messages",
                    "source_column": "interview_id",
                    "target_table": "interviews",
                    "target_column": "id",
                    "on_delete": "CASCADE"
                },
                {
                    "source_table": "code_submissions",
                    "source_column": "interview_id",
                    "target_table": "interviews",
                    "target_column": "id",
                    "on_delete": "CASCADE"
                }
            ],
            "isolated_tables": [
                {
                    "table": "alembic_version",
                    "notes": "Standalone single-row table tracking SQLAlchemy Alembic migration version. Currently at '004_assessment_extensions'."
                },
                {
                    "table": "document_embeddings",
                    "notes": "Completely disconnected from the relational schema. Has ZERO foreign keys. Not tracked by Alembic migrations (created via manual alembic/pgvector_setup.sql). Interfaced exclusively via RAGService/SupabaseVectorRetriever at runtime."
                }
            ],
            "application_relationships": {
                "document_embeddings_to_interview": "No DB foreign key. Application connects them purely in memory: during interview turn, InterviewService queries document_embeddings via RAGService using role and difficulty filters, constructs QuestionCandidate, and if selected, writes the text to interview_messages.question."
            }
        },
        "part_3_document_embeddings_audit": {
            "total_rows": 9394,
            "populated_embeddings": 4630,
            "null_embeddings": 4764,
            "status_breakdown": {
                "inactive": 7664,
                "null_or_unspecified": 1730,
                "active": 0
            },
            "quality_classifications": raw_data["document_embeddings_audit"]["classification_breakdown"],
            "classification_examples": raw_data["document_embeddings_audit"]["classification_examples"]
        },
        "part_4_actual_dataset_schema": deep_data["field_stats"],
        "part_5_skill_analysis": {
            "total_distinct_topics": len(deep_data["topic_distribution"]),
            "top_topics": list(deep_data["topic_distribution"].items())[:30],
            "findings": [
                "There is NO 'skill' or 'technology' field in document_embeddings metadata. The null rate is 100%.",
                "Topic is an ad-hoc compound string blending technology, domain, and exercise type (e.g., 'Python Algorithms & Data Structures', 'Bash & Automation Scripts').",
                "Subtopic field was corrupted during ingestion: contains 6,571 distinct values, many of which are raw markdown headers like '## Answer: 1', '## Answer: 4'.",
                "Extreme frequency imbalance: 'Python Algorithms & Data Structures' has 2,272 records (24.2% of the dataset), while 40+ topics have fewer than 15 records."
            ]
        },
        "part_6_question_quality_analysis": {
            "text_patterns": deep_data["text_patterns"],
            "defect_samples": defects_data
        },
        "part_7_difficulty_analysis": {
            "distribution": deep_data["difficulty_distribution"],
            "findings": [
                "Difficulty values: Easy: 3818, Hard: 3677, Medium: 1893, Null: 6.",
                "Difficulty assignment was unscientific and flawed: in download_and_clean_real_dataset.py, difficulty was assigned purely based on character length (>800 chars -> Hard, >350 chars -> Medium, <=350 chars -> Easy).",
                "In dataset_generator.py, difficulty was assigned in a round-robin loop: [Easy, Medium, Hard][i % 3]. This resulted in identical questions being duplicated with Easy, Medium, and Hard labels."
            ]
        },
        "part_8_role_analysis": {
            "distribution": deep_data["role_distribution"],
            "findings": [
                "10 canonical roles present in metadata: Python Developer (2583), Frontend Developer (2470), Java Developer (920), Database Developer (735), DevOps / Cloud Engineer (625), Backend Developer (571), Data Analyst (397), AI Engineer (385), Machine Learning Engineer (374), Full Stack Developer (328).",
                "Crucial bug discovered: metadata stores 'role' as Title Case ('Backend Developer') and 'role_id' as snake_case ('backend_developer'). Application code filters on {'role': mapped_role} with snake_case, causing RAG queries with role filters to return 0 records."
            ]
        },
        "part_9_category_intent_strategy_analysis": {
            "category_distribution": deep_data["category_distribution"],
            "findings": [
                "Categories in DB: 'Coding' (5313), 'Theory' (4075), with 5 outlier records.",
                "Fields 'intent' and 'strategy' DO NOT EXIST in document_embeddings metadata (100% missing).",
                "The rich taxonomy used by QuestionQualityEvaluator (CAT_ARCHITECTURE, CAT_DATA_FLOW, etc.) and STRATEGY_TO_INTENT has NO representation in the question bank."
            ]
        },
        "part_10_embedding_audit": {
            "dimensions": 1536,
            "populated_count": 4630,
            "null_count": 4764,
            "findings": [
                "Embedding model is gemini-embedding-2 (1536 dims). Not stored in metadata.",
                "All 4,630 existing embeddings represent the FULL polluted document content (markdown headers, model answers, code blocks, and rubrics), NOT clean interview questions.",
                "Embeddings cannot be reused after question extraction/normalization."
            ]
        },
        "part_11_duplicate_analysis": dups_data,
        "part_12_other_tables_audit": {
            "interviews": {
                "row_count": 139,
                "roles_sample": ["Backend Developer", "Frontend developer", "SOFTWARE ENGINEER", "Software Developer"],
                "status_distribution": {"ACTIVE": 95, "COMPLETED": 44}
            },
            "interview_messages": {
                "row_count": 278,
                "null_question_type_rate": "238 / 278 (85.6%)",
                "findings": "Historical interview_messages contained severe prompt leakage where fallback prompt text leaked into candidate questions."
            },
            "code_submissions": {
                "row_count": 0,
                "notes": "Table exists with schema (interview_id, problem_id, language, source_code, result), but currently has 0 rows."
            }
        },
        "part_13_application_db_mapping": {
            "retrieval_flow": "InterviewService -> RAGService -> SupabaseVectorRetriever -> match_document_embeddings_filtered RPC -> document_embeddings",
            "schema_mismatches": [
                "Role filter mismatch: code passes snake_case to 'role', DB has Title Case in 'role' and snake_case in 'role_id'.",
                "Content mismatch: code expects a clean question text, DB stores full tutorial/rubric article.",
                "Difficulty mismatch: code requests difficulty filtering, but DB difficulty was assigned by character length or round-robin modulo.",
                "Taxonomy mismatch: code has 10 categories, DB only has 'Coding' vs 'Theory'."
            ]
        },
        "part_14_canonical_contract_recommendation": {
            "recommended_schema": {
                "required": ["id", "question", "role_id", "primary_skill", "difficulty", "category", "intent"],
                "optional": ["secondary_skills", "technologies", "expected_answer", "evaluation_rubric", "source", "author"],
                "derived": ["embedding", "embedding_model", "token_count", "created_at", "updated_at"],
                "not_needed": ["full_markdown_article", "unstructured_content_dump"]
            }
        },
        "part_15_problems_division": {
            "dataset_problems": [
                "93% of document_embeddings content is polluted with markdown articles, model answers, and rubrics rather than clean questions.",
                "The 689 normalized questions are 100% identical synthetic template variations with broken punctuation.",
                "Difficulty ratings are artificial (based on char length or round-robin modulo).",
                "Duplicate groups exist across Easy, Medium, and Hard tags.",
                "Subtopics are corrupted with markdown strings like '## Answer: 1'.",
                "Category is virtually binary ('Coding' vs 'Theory').",
                "No 'skill' or 'technology' fields exist in metadata.",
                "Real interview questions from GitHub repositories remain unextracted or quarantined as tutorials."
            ],
            "code_problems": [
                "RAG filter bug: filters['role'] = mapped_role (snake_case) fails against Title Case metadata['role'].",
                "RAG retrieval query mixes strategy and category into the embedding search string.",
                "RAG top-k was previously 2 before Phase 1 widening.",
                "Lack of structured schema enforcement when ingesting dataset.",
                "Prompt leakage in fallback question generator.",
                "No validation preventing multi-paragraph text from becoming a QuestionCandidate."
            ]
        },
        "part_16_recommendation": {
            "status": "STOP_AND_REDESIGN",
            "recommendation_summary": "Do NOT proceed with Phase 4.4 embedding regeneration for the 689 records. The 689 records are 100% synthetic template sentences with broken punctuation. Regenerating embeddings would waste Gemini quota on low-quality synthetic data. The dataset must be properly restructured into canonical question records first."
        }
    }
    
    out_file = "reports/database_dataset_forensic_audit.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_json, f, indent=2)
    print(f"Saved full audit JSON to {out_file}")

if __name__ == "__main__":
    build_full_audit_json()
