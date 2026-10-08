import os
import sys
import json
import asyncio
import google.generativeai as genai

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.key_pool import gemini_key_pool

async def test_key(key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-3.8-flash")
    try:
        res = await asyncio.to_thread(model.generate_content, "Say hello")
        return {"status": "SUCCESS", "response": res.text}
    except Exception as e:
        err_type = gemini_key_pool.classify_error(e)
        return {
            "status": "ERROR",
            "exception_type": type(e).__name__,
            "message": str(e),
            "classified_as": err_type
        }

async def main():
    keys = gemini_key_pool.keys
    print(f"Testing {len(keys)} configured keys sequentially...")
    results = []
    
    for i, k in enumerate(keys):
        print(f"Testing Key {i}...")
        res = await test_key(k)
        results.append({"index": i, "result": res})
        print(res)
        
    with open("reports/phase4d_quota_incident_report.json", "w") as f:
        json.dump({
            "root_cause_analysis": "Pending review",
            "keys_configured": len(keys),
            "key_test_results": results
        }, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
