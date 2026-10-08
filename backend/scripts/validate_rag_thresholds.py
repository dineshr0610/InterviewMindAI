import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from ai_engine.vectorstores.supabase_store import SupabaseVectorRetriever

def validate_thresholds():
    # Evaluate a relaxed threshold to fetch the raw distribution
    retriever = SupabaseVectorRetriever(k=10, similarity_threshold=0.0)
    
    test_cases = [
        {
            "query": "How do you implement dependency injection in FastAPI?",
            "role": "Python Developer",
            "expected_keywords": ["FastAPI", "dependency injection", "yield"],
        },
        {
            "query": "What is the difference between a process and a thread?",
            "role": "Backend Developer",
            "expected_keywords": ["process", "thread", "memory", "concurrency"],
        },
        {
            "query": "Explain CSS Flexbox vs Grid.",
            "role": "Frontend Developer",
            "expected_keywords": ["flexbox", "grid", "1D", "2D", "layout"],
        }
    ]
    
    thresholds = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65]
    
    print("=== SIMILARITY THRESHOLD VALIDATION ===")
    
    for case in test_cases:
        print(f"\n[QUERY] {case['query']}")
        print(f"Role Filter: {case['role']}")
        
        # We fetch up to 10 results at threshold 0.0 to see the natural distribution
        docs = retriever.get_filtered_documents(case['query'], metadata_filter={"role": case['role']})
        
        if not docs:
            print("  No documents found for this query/role in the current dataset.")
            continue
            
        print("  Distribution of Top 5 Results:")
        for i, doc in enumerate(docs[:5]):
            sim = doc.metadata.get("similarity", 0.0)
            # Evaluate relevance heuristically based on expected keywords
            content_lower = doc.page_content.lower()
            matched = [k for k in case['expected_keywords'] if k.lower() in content_lower]
            relevance = "HIGH" if len(matched) >= 2 else "LOW" if len(matched) == 0 else "MEDIUM"
            print(f"    {i+1}. Sim: {sim:.3f} | Rel: {relevance} | Matches: {matched}")
            
        print("\n  Threshold Impact Analysis:")
        for t in thresholds:
            passed = [d for d in docs if d.metadata.get("similarity", 0.0) >= t]
            
            # Calculate precision/recall metrics based on our heuristic 'HIGH/MEDIUM'
            relevant_retrieved = sum(1 for d in passed if sum(1 for k in case['expected_keywords'] if k.lower() in d.page_content.lower()) >= 1)
            total_retrieved = len(passed)
            
            precision = (relevant_retrieved / total_retrieved) if total_retrieved > 0 else 0
            
            print(f"    Threshold {t:.2f} -> Retained: {total_retrieved}/{len(docs)} | Est. Precision: {precision:.2f}")

if __name__ == "__main__":
    validate_thresholds()
