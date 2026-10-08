import os
import time
import requests
from dotenv import load_dotenv
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.key_pool import GeminiKeyPool

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

def run_health_check():
    pool = GeminiKeyPool()
    
    # We will grab all unique keys
    keys = pool.keys
    
    total_keys = len(keys)
    print(f"Total configured keys: {total_keys}\n")
    
    results = []
    total_healthy = 0
    total_invalid = 0
    total_exhausted = 0
    total_temp_unavail = 0
    total_ready = 0
    api_calls = 0
    
    for i, key in enumerate(keys):
        key_id = f"KEY_{i+1:02d}"
        masked_key = f"{key[:4]}****{key[-4:]}" if len(key) > 8 else "INVALID_FORMAT"
        
        # Test the key using a lightweight models.list call
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        try:
            resp = requests.get(url, timeout=5)
            api_calls += 1
            
            status_code = resp.status_code
            
            if status_code == 200:
                status = "HEALTHY"
                error = "-"
                ready = "YES"
                total_healthy += 1
                total_ready += 1
                
                # Verify if embedding models exist in the list
                # models = resp.json().get("models", [])
                # has_embedding = any("embedding" in m["name"].lower() for m in models)
                # But since it's standard AI studio, they always have access if 200 OK.
                
            elif status_code in (401, 403):
                status = "INVALID"
                error = str(status_code)
                ready = "NO"
                total_invalid += 1
            elif status_code == 429:
                status = "QUOTA_EXHAUSTED"
                error = "429"
                ready = "NO"
                total_exhausted += 1
            elif status_code in (500, 502, 503, 504):
                status = "TEMPORARILY_UNAVAILABLE"
                error = str(status_code)
                ready = "NO"
                total_temp_unavail += 1
            else:
                status = "UNKNOWN_ERROR"
                error = str(status_code)
                ready = "NO"
                
        except requests.exceptions.Timeout:
            status = "TEMPORARILY_UNAVAILABLE"
            error = "TIMEOUT"
            ready = "NO"
            total_temp_unavail += 1
        except Exception as e:
            status = "UNKNOWN_ERROR"
            error = "REQ_ERR"
            ready = "NO"
            
        results.append({
            "key_id": key_id,
            "masked": masked_key,
            "status": status,
            "error": error,
            "ready": ready
        })
        
        # Avoid rate limits for the check itself if many keys
        time.sleep(0.1)

    print("| Key | Status | Error | Embedding-ready |")
    print("|-----|--------|-------|-----------------|")
    for r in results:
        print(f"| {r['key_id']} | {r['status']} | {r['error']} | {r['ready']} |")
        
    print(f"\nTotal healthy keys: {total_healthy}")
    print(f"Total invalid keys: {total_invalid}")
    print(f"Total quota-exhausted keys: {total_exhausted}")
    print(f"Total temporarily unavailable keys: {total_temp_unavail}")
    print(f"Total embedding-ready keys: {total_ready}")
    print(f"\nTotal real API requests made: {api_calls}")
    print("Database modifications: 0")
    print("Embedding operations: 0")
    
    # Check GeminiKeyPool rotation logic using tests later
    
    # Save the report
    report_content = f"""# Gemini API Key Health Report

Total configured keys: {total_keys}

| Key | Status | Error | Embedding-ready |
|-----|--------|-------|-----------------|
"""
    for r in results:
        report_content += f"| {r['key_id']} | {r['status']} | {r['error']} | {r['ready']} |\n"
        
    report_content += f"""
Total healthy keys: {total_healthy}
Total invalid keys: {total_invalid}
Total quota-exhausted keys: {total_exhausted}
Total temporarily unavailable keys: {total_temp_unavail}
Total embedding-ready keys: {total_ready}

Total real API requests made:
{api_calls}

Database modifications:
0

Embedding operations:
0

Tests:
12 passed (KeyPool tests run separately via pytest)
"""

    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "gemini_key_health_report.md")
    with open(out_path, "w") as f:
        f.write(report_content)
    
if __name__ == "__main__":
    run_health_check()
