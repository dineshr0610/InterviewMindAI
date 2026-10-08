import sys
import os
from pathlib import Path
import time
import json

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from ai_engine.services.interview_service import InterviewService
from ai_engine.services.question_controller import choose_next_strategy

def simulate_answer(q: str, difficulty: str) -> str:
    """Return a decent simulated candidate answer to encourage varying strategies."""
    if "how did you" in q.lower() or "why did you" in q.lower() or "explain" in q.lower():
        return "I structured it using modular components. We had a tradeoff with latency, so we added a caching layer and decoupled the intensive parts into background workers. We handled failures using retries and exponential backoff."
    elif "edge case" in q.lower() or "failure" in q.lower():
        return "For that specific edge case, we implemented circuit breakers and fallback defaults so the user experience wouldn't be completely interrupted."
    else:
        return "Yes, we used that extensively to solve our immediate requirements and scale the system."

def run_simulation(role: str, resume_text: str, projects: list, technologies: list, missing: list):
    service = InterviewService()
    
    state = {
        "score": 5,
        "difficulty": "Medium",
        "current_objective": "assess_role_competency",
        "topics_covered": [],
        "categories_covered": [],
        "projects_covered": [],
        "technologies_covered": [],
        "missing_skills_covered": [],
        "recent_question_intents": [],
        "follow_up_depth": 0,
        "topic_inventory": {
            "projects": projects,
            "technologies": technologies
        }
    }
    
    resume_match = {
        "role": role,
        "matched_skills": technologies,
        "matched_technologies": technologies,
        "matched_projects": projects,
        "missing_skills": missing,
        "evidence": ["Verified via resume"]
    }
    
    previous_questions = []
    results = []
    
    print(f"=== Starting Interview Simulation for {role} ===")
    
    strategy = "topic_transition"
    last_answer = None
    
    for turn in range(1, 6):
        start_t = time.time()
        
        # Simulate interview progression logic
        q_result = service.generate_question(
            topic=state["topics_covered"][-1] if state["topics_covered"] else technologies[0],
            difficulty=state["difficulty"],
            previous_questions=previous_questions,
            focus="technical",
            resume_text=resume_text,
            strategy=strategy,
            last_answer=last_answer,
            role=role,
            resume_match=resume_match,
            interview_phase="resume_phase",
            state=state,
        )
        
        latency = time.time() - start_t
        q_text = q_result.get("question", "")
        metadata = q_result.get("metadata", {})
        
        q_source = metadata.get("source", "unknown")
        q_topic = metadata.get("topic", "unknown")
        q_tech = metadata.get("technology", "")
        q_proj = metadata.get("project", "")
        q_intent = metadata.get("intent", "unknown")
        q_diff = metadata.get("difficulty", state["difficulty"])
        q_cat = metadata.get("category", "")
        
        # Record
        results.append({
            "turn": turn,
            "source": q_source,
            "project": q_proj,
            "technology": q_tech,
            "topic": q_topic,
            "intent": q_intent,
            "difficulty": q_diff,
            "category": q_cat,
            "latency": latency,
            "follow_up_depth": state["follow_up_depth"]
        })
        
        previous_questions.append(q_text)
        
        # Update State
        if q_topic and q_topic not in state["topics_covered"]:
            state["topics_covered"].append(q_topic)
        if q_cat and q_cat not in state["categories_covered"]:
            state["categories_covered"].append(q_cat)
        if q_proj and q_proj not in state["projects_covered"]:
            state["projects_covered"].append(q_proj)
        if q_tech and q_tech not in state["technologies_covered"]:
            state["technologies_covered"].append(q_tech)
        if q_source == "missing_skill" and q_topic not in state["missing_skills_covered"]:
            state["missing_skills_covered"].append(q_topic)
            
        state["recent_question_intents"].append(q_intent)
        
        # Simulate Candidate Answer and score
        last_answer = simulate_answer(q_text, q_diff)
        state["score"] = 8 if turn % 3 == 0 else 6 # Fluctuate score
        
        # Adaptive logic
        if state["score"] >= 8:
            if state["difficulty"] == "Easy": state["difficulty"] = "Medium"
            elif state["difficulty"] == "Medium": state["difficulty"] = "Hard"
        elif state["score"] <= 4:
            if state["difficulty"] == "Hard": state["difficulty"] = "Medium"
            elif state["difficulty"] == "Medium": state["difficulty"] = "Easy"
            
        strategy = choose_next_strategy(state["score"], state["follow_up_depth"])
        if strategy in ("follow_up", "clarification", "deeper_probe", "edge_case", "tradeoff", "scenario", "architecture"):
            state["follow_up_depth"] += 1
        else:
            state["follow_up_depth"] = 0

    # Print summary
    print(f"\\n--- {role} Results ---")
    sources = {}
    intents = set()
    projects_covered = set()
    techs_covered = set()
    total_latency = 0
    
    for r in results:
        sources[r['source']] = sources.get(r['source'], 0) + 1
        intents.add(r['intent'])
        if r['project']: projects_covered.add(r['project'])
        if r['technology']: techs_covered.add(r['technology'])
        total_latency += r['latency']
        print(f"Turn {r['turn']}: [{r['source']}] (Diff: {r['difficulty']}, Depth: {r['follow_up_depth']}) Tech: {r['technology']} | Proj: {r['project']} | Intent: {r['intent']} | Latency: {r['latency']:.1f}s")
        
    print("\\nMetrics:")
    print(f"- Unique Projects Covered: {len(projects_covered)} / {len(projects)}")
    print(f"- Unique Technologies Covered: {len(techs_covered)} / {len(technologies)}")
    print(f"- Intent Diversity: {len(intents)}")
    print(f"- Sources: {sources}")
    print(f"- Average Latency: {total_latency/15:.1f}s\\n")

if __name__ == "__main__":
    import asyncio
    
    # 1. Frontend Developer
    run_simulation(
        role="Frontend Developer",
        resume_text="Experienced Frontend Developer building UIs with React, Redux, and CSS. I use Webpack and Jest.",
        projects=[
            {"name": "E-Commerce Dashboard", "evidence": "Built a scalable dashboard using React and Redux."},
            {"name": "Marketing Site", "evidence": "Developed responsive UI with CSS Grid and animations."}
        ],
        technologies=["React", "Redux", "CSS", "HTML", "JavaScript", "Webpack", "Jest", "Git", "Jira"],
        missing=["TypeScript", "GraphQL"]
    )
    
    # 2. Backend Developer
    run_simulation(
        role="Backend Developer",
        resume_text="Backend engineer using Python, PostgreSQL, and Docker. Built REST APIs and microservices.",
        projects=[
            {"name": "Payment Gateway", "evidence": "Built resilient payment processor with Python and Redis."},
            {"name": "User Auth Service", "evidence": "Implemented OAuth2 using PostgreSQL and Python."}
        ],
        technologies=["Python", "PostgreSQL", "Redis", "Docker", "REST API", "SQL", "Git", "Linux", "Slack"],
        missing=["Kubernetes", "gRPC"]
    )
    
    # 3. Full Stack Developer
    run_simulation(
        role="Full Stack Developer",
        resume_text="Full stack developer using Node.js, React, and MongoDB. Built scalable web applications from scratch.",
        projects=[
            {"name": "Real-time Chat", "evidence": "Built real-time messaging using WebSockets, Node.js and React."},
            {"name": "Inventory Manager", "evidence": "Full stack inventory system with MongoDB and Express."}
        ],
        technologies=["Node.js", "React", "MongoDB", "Express", "WebSockets", "JavaScript", "Docker", "Nginx", "Agile"],
        missing=["PostgreSQL", "CI/CD"]
    )
