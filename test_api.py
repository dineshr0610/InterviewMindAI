import httpx
import json

def test_analyze():
    url = "http://localhost:8000/api/interview/resume/analyze"
    with open("test_resume.txt", "r") as f:
        resume_text = f.read()
    
    data = {
        "role": "Software Engineer",
        "resume_text": resume_text,
        "candidate_name": "John Doe"
    }
    
    response = httpx.post(url, json=data, timeout=120.0)
    print("Status Code:", response.status_code)
    try:
        with open("test_api_response.json", "w") as out:
            json.dump(response.json(), out, indent=2)
        print("Saved response to test_api_response.json")
    except Exception as e:
        print("Response text:", response.text)

if __name__ == "__main__":
    test_analyze()
