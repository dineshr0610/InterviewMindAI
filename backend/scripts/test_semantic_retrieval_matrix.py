import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from ai_engine.vectorstores.supabase_store import SupabaseVectorRetriever

def run_test_matrix():
    retriever = SupabaseVectorRetriever(k=3, similarity_threshold=0.3)
    
    matrix = [
        # BACKEND
        {"query": "Explain how GIL works in Python.", "role": "Backend Developer", "tech": "Python", "diff": "Medium"},
        {"query": "How do you handle routing in Flask?", "role": "Backend Developer", "tech": "Flask", "diff": "Easy"},
        {"query": "What are dependencies in FastAPI?", "role": "Backend Developer", "tech": "FastAPI", "diff": "Medium"},
        {"query": "How do you optimize a slow query in PostgreSQL?", "role": "Backend Developer", "tech": "PostgreSQL", "diff": "Hard"},
        {"query": "Explain cache eviction policies in Redis.", "role": "Backend Developer", "tech": "Redis", "diff": "Medium"},
        {"query": "What is REST API design?", "role": "Backend Developer", "tech": "API design", "diff": "Easy"},
        {"query": "How do you implement OAuth2?", "role": "Backend Developer", "tech": "authentication", "diff": "Hard"},
        {"query": "Explain database indexing strategies.", "role": "Backend Developer", "tech": "database indexing", "diff": "Medium"},
        {"query": "How to handle high concurrency?", "role": "Backend Developer", "tech": "concurrency", "diff": "Hard"},
        
        # FRONTEND
        {"query": "How does React Virtual DOM work?", "role": "Frontend Developer", "tech": "React", "diff": "Medium"},
        {"query": "Explain closures in JavaScript.", "role": "Frontend Developer", "tech": "JavaScript", "diff": "Medium"},
        {"query": "What are TypeScript generics?", "role": "Frontend Developer", "tech": "TypeScript", "diff": "Medium"},
        {"query": "Explain CSS Flexbox vs Grid.", "role": "Frontend Developer", "tech": "CSS", "diff": "Easy"},
        {"query": "How do you manage global state?", "role": "Frontend Developer", "tech": "state management", "diff": "Medium"},
        {"query": "What is component-driven architecture?", "role": "Frontend Developer", "tech": "component architecture", "diff": "Medium"},
        {"query": "How do you optimize web performance?", "role": "Frontend Developer", "tech": "performance", "diff": "Hard"},
        {"query": "What are ARIA attributes?", "role": "Frontend Developer", "tech": "accessibility", "diff": "Medium"}
    ]
    
    print("=== SEMANTIC RETRIEVAL TEST MATRIX ===")
    
    for case in matrix:
        print(f"\n[TEST] {case['query']}")
        print(f"  Target Role: {case['role']} | Diff: {case['diff']}")
        
        docs = retriever.get_filtered_documents(
            case['query'], 
            metadata_filter={"role": case['role'], "difficulty": case['diff']}
        )
        
        if not docs:
            print("  -> Result: 0 documents retrieved (Need full backfill)")
            continue
            
        top_doc = docs[0]
        top_sim = top_doc.metadata.get("similarity", 0.0)
        top_role = top_doc.metadata.get("role", "")
        
        print(f"  -> Top Similarity: {top_sim:.3f}")
        print(f"  -> Top Result Role Correctness: {'PASS' if top_role == case['role'] else 'FAIL (Got: ' + top_role + ')'}")
        print(f"  -> Top Result Excerpt: {top_doc.page_content[:100]}...")
        
        print(f"  -> Top 3 Results Overview:")
        for i, d in enumerate(docs):
            sim = d.metadata.get("similarity", 0.0)
            print(f"       {i+1}. Sim {sim:.3f}: {d.page_content[:50]}...")

if __name__ == "__main__":
    run_test_matrix()
