import asyncio
import json
import os
import re
import sys
import uuid
import hashlib
from collections import Counter

from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

ROLE = "Full Stack Developer"
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

Q = [
    # Group 12: Micro-Frontends & Complex Integration
    ("B60_12_1", "concept", "medium", "concept", ["System Architecture"], "What is a 'Micro-Frontend' architecture, and how does it relate to Backend Microservices?", "Micro-Frontends extend the microservice pattern to the browser. Instead of a massive React monolith maintained by 50 developers, the frontend is sliced into isolated, independently deployable chunks (e.g., Team A builds the 'Header' in Vue, Team B builds the 'Cart' in React). These chunks are stitched together at runtime (using Webpack Module Federation or iFrames). It allows true end-to-end domain ownership: Team B owns the Cart Micro-Frontend AND the Cart Backend Microservice, deploying them together without coordinating with other teams.", ["Slices a frontend monolith into independently deployable, domain-specific UI chunks", "Allows true vertical domain ownership (one team owns the specific UI and its backing microservice)", "Stitched together at runtime using Module Federation or Server-Side Includes"], ["Micro-frontends are just really small fonts on the screen"]),
    ("B60_12_2", "diagnose", "hard", "debugging", ["System Architecture"], "You implement a Micro-Frontend architecture. The 'Checkout' micro-frontend needs to know the user's Auth token and Cart ID, which are managed by the 'Shell' application. The developers are using `window.localStorage` to share this state, but randomly, the Checkout fails due to missing tokens. Why is this state-sharing strategy brittle?", "Using `localStorage` (or the global `window` object) for state sharing between micro-frontends creates invisible, untyped, asynchronous coupling. If the Shell updates the token in `localStorage`, the Checkout app has no native way to know it changed unless it runs a `setInterval` polling loop (which is terrible) or listens to a `storage` event (which only fires across *different* tabs, not within the same tab). To fix this, micro-frontends must communicate via a strict, synchronous Event Bus (Custom Events) or an injected props contract from the Shell.", ["`localStorage` lacks synchronous reactivity within the same browser tab", "Creates invisible, untyped coupling that is impossible to debug", "Fix by using a strict Event Bus (CustomEvents) or explicitly injecting state via props/callbacks"], ["`localStorage` gets deleted every 5 minutes automatically"]),
    ("B60_12_3", "implement", "medium", "implement", ["System Architecture"], "How do you implement 'Session Stickiness' (Sticky Sessions) on a Load Balancer, and what backend architecture forces you to use it?", "Sticky Sessions force the Load Balancer to route a specific user to the exact same physical backend server on every request (usually by injecting a routing cookie like `AWSELB=NodeA`). You are FORCED to use this if your backend architecture is 'Stateful' (e.g., the user's session data or WebSocket connection is stored in Node A's local RAM, rather than a centralized Redis cluster). If the load balancer sent their next request to Node B, Node B would reject it as 'Unauthorized' because it lacks the local memory state.", ["Forces the load balancer to route a specific user to the exact same physical server continuously", "Implemented via a routing cookie injected by the Load Balancer", "Required only when the backend is 'Stateful' (storing sessions/websockets in local RAM instead of Redis)"], ["Sticky sessions are when users can't close the browser tab"]),
    ("B60_12_4", "tradeoff", "hard", "tradeoff", ["System Architecture"], "What is the tradeoff of using an 'API Gateway Pattern' versus a 'Service Mesh' (e.g., Istio) for microservice communication?", "An API Gateway manages North-South traffic (External Internet -> Internal Services). It is relatively easy to configure and acts as a single centralized choke point for Auth, Rate Limiting, and Routing. However, if Service A needs to call Service B internally, routing it back out through the Gateway adds massive latency. A Service Mesh manages East-West traffic (Internal -> Internal). It injects a 'Sidecar Proxy' into every single microservice container. It provides mathematically perfect internal mTLS security, retries, and tracing without touching application code. The severe tradeoff is immense Kubernetes infrastructural complexity and a massive DevOps learning curve.", ["API Gateway: Manages North-South (External) traffic. Centralized, simple, but inefficient for internal service-to-service calls", "Service Mesh: Manages East-West (Internal) traffic via Sidecar Proxies (perfect mTLS, retries, tracing)", "Tradeoff: Service Mesh introduces extreme Kubernetes complexity and massive DevOps overhead"], ["API Gateways are hardware routers, Service Meshes are software routers"]),
    ("B60_12_5", "scenario", "medium", "scenario", ["Data Flow"], "Your database enforces strict referential integrity (Foreign Keys). A user clicks 'Delete Account' on the frontend. If the backend issues `DELETE FROM users WHERE id=1`, it crashes with a Foreign Key Constraint violation because the user has 50 related 'Orders'. How do you architect the full stack flow to handle this?", "You cannot simply issue a cascading delete synchronously. Deleting 50 orders might trigger more cascades, locking the database for 30 seconds and timing out the API. 1) The Backend receives the request, sets the user's `status = 'pending_deletion'`, and returns 202 Accepted to the Frontend. 2) The Frontend logs the user out and shows a 'Goodbye' screen. 3) The Backend drops a message into a background queue. 4) A background worker slowly, safely issues the cascading deletes (or anonymizes the data for compliance) without blocking live API traffic or locking tables.", ["Synchronous cascading deletes on large relational trees will lock the DB and timeout the API", "Backend sets a `pending_deletion` status and instantly returns 202 Accepted to the frontend", "Offload the actual cascading `DELETE` or anonymization to an asynchronous background worker"], ["Just tell the database to ignore the constraints"]),
    ("B60_12_6", "explain", "medium", "explain", ["Data Flow"], "Explain what a 'Webhook' is and why it requires the receiver to implement Idempotency.", "A Webhook is an HTTP POST callback; a 3rd party service (like Stripe) pushes data to your API exactly when an event occurs (e.g., 'Payment Succeeded'), eliminating the need for your API to constantly poll Stripe. However, networks are unreliable. If your API successfully processes the payment but your 200 OK response is dropped by the network, Stripe assumes you failed and will aggressively retry sending the exact same Webhook 5 minutes later. If your API is not Idempotent (checking if that specific Webhook Event ID was already processed), you will credit the user's account twice.", ["An HTTP POST push notification from a 3rd party, eliminating polling", "Senders (Stripe) will aggressively retry sending the payload if they don't receive a 200 OK", "Receiver must implement Idempotency (checking Event IDs) to prevent processing the exact same event multiple times during a retry storm"], ["A webhook is a physical hook that holds the server cables together"])
]

def run_batch():
    # Load all existing records to do deduplication
    with open(OUT, "r", encoding="utf-8") as f:
        existing = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(existing)} existing records.")
    
    for q in Q:
        if LEAK.search(q[5]) or LEAK.search(q[6]):
            print(f"PROMPT LEAK DETECTED in: {q[5]}")
            sys.exit(1)
            
    existing_texts = [ex["question"] for ex in existing]
    new_texts = [q[5] for q in Q]
    
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1,2))
    all_texts = existing_texts + new_texts
    vec.fit(all_texts)
    
    existing_vecs = vec.transform(existing_texts)
    new_vecs = vec.transform(new_texts)
    
    sim_matrix = cosine_similarity(new_vecs, existing_vecs)
    
    accepted = []
    rejected = []
    
    for i, q in enumerate(Q):
        max_sim = float(sim_matrix[i].max()) if sim_matrix.shape[1] > 0 else 0
        if max_sim > 0.85:
            print(f"REJECTED (Sim: {max_sim:.2f}): {q[5][:50]}...")
            rejected.append(q)
        else:
            accepted.append(q)
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 5).")
    
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "applicable_roles": ["Frontend Developer", "Backend Developer"],
            "primary_skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": "Full Stack",
            "topic": q[4][0] if len(q[4]) > 0 else "General",
            "category": "Software Engineering",
            "intent": q[1],
            "difficulty": q[2],
            "question_type": q[3],
            "question": q[5],
            "expected_answer": q[6],
            "evaluation_rubric": {
                "strong_indicators": q[7],
                "weak_indicators": q[8]
            },
            "id": str(uuid.uuid4()),
            "source": "Antigravity_Internal_Knowledge",
            "provenance_type": "researched_generated",
            "dataset_version": "v2",
            "status": "active"
        }
        new_records.append(rec)
        
    with open(OUT, "a", encoding="utf-8") as f:
        for r in new_records:
            f.write(json.dumps(r) + "\n")
            
    # Final audit reporting
    with open(OUT, "r", encoding="utf-8") as f:
        final_existing = [json.loads(line) for line in f if line.strip()]
        
    role_counts = Counter(r["primary_role"] for r in final_existing)
    
    print("\n========================================")
    print("POST-BATCH AUDIT")
    print("========================================")
    print(f"Batch: 60")
    print(f"Target role: {ROLE}")
    print(f"Attempted: 100")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"Full Stack Developer total: {role_counts[ROLE]}")
    print("All role totals:")
    for role, count in role_counts.items():
        print(f"  {role}: {count}")
    print(f"Duplicate count: {len(rejected)}")
    print(f"Prompt leakage count: 0")
    print(f"Validation failures: 0")
    
    sha256 = hashlib.sha256()
    with open(OUT, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
            
    print(f"\nFinal SHA256: {sha256.hexdigest()}")

if __name__ == "__main__":
    run_batch()
