"""Role-specific coding problems and local Python execution.

External multi-language execution (Judge0, Docker sandboxes, etc.) is not a
current project dependency. Python problems run in a subprocess with a timeout.
Other languages return a structured 'runtime unavailable' result plus static review.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional


CODING_PROBLEMS: List[Dict[str, Any]] = [
    {
        "id": "two_sum",
        "roles": ["software_engineer", "backend_developer", "full_stack_developer", "frontend_developer"],
        "coding_topic": "hash maps",
        "problem_type": "algorithms",
        "difficulty": "Easy",
        "language": "python",
        "title": "Two Sum",
        "statement": (
            "Given a list of integers nums and an integer target, return the indices of "
            "the two numbers that add up to target. You may assume exactly one solution "
            "exists and you may not use the same element twice."
        ),
        "input": "nums: list[int], target: int",
        "output": "list[int] of two indices",
        "constraints": "2 <= len(nums) <= 10^4; exactly one valid pair",
        "function_name": "two_sum",
        "starter": "def two_sum(nums, target):\n    pass\n",
        "tests": [
            {"args": [[2, 7, 11, 15], 9], "expected": [0, 1]},
            {"args": [[3, 2, 4], 6], "expected": [1, 2]},
            {"args": [[3, 3], 6], "expected": [0, 1]},
        ],
    },
    {
        "id": "valid_parentheses",
        "roles": ["software_engineer", "backend_developer", "full_stack_developer"],
        "coding_topic": "stacks",
        "problem_type": "algorithms",
        "difficulty": "Easy",
        "language": "python",
        "title": "Valid Parentheses",
        "statement": (
            "Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', "
            "determine if the input string is valid. Brackets must close in the correct order."
        ),
        "input": "s: str",
        "output": "bool",
        "constraints": "1 <= len(s) <= 10^4",
        "function_name": "is_valid",
        "starter": "def is_valid(s):\n    pass\n",
        "tests": [
            {"args": ["()"], "expected": True},
            {"args": ["()[]{}"], "expected": True},
            {"args": ["(]"], "expected": False},
            {"args": ["([)]"], "expected": False},
        ],
    },
    {
        "id": "longest_unique",
        "roles": ["frontend_developer", "full_stack_developer", "software_engineer"],
        "coding_topic": "strings",
        "problem_type": "algorithms",
        "difficulty": "Medium",
        "language": "python",
        "title": "Longest Substring Without Repeating Characters",
        "statement": (
            "Given a string s, return the length of the longest substring without repeating characters."
        ),
        "input": "s: str",
        "output": "int",
        "constraints": "0 <= len(s) <= 5 * 10^4",
        "function_name": "length_of_longest_substring",
        "starter": "def length_of_longest_substring(s):\n    pass\n",
        "tests": [
            {"args": ["abcabcbb"], "expected": 3},
            {"args": ["bbbbb"], "expected": 1},
            {"args": ["pwwkew"], "expected": 3},
            {"args": [""], "expected": 0},
        ],
    },
    {
        "id": "group_by_key",
        "roles": ["data_engineer", "data_analyst", "data_scientist", "machine_learning_engineer"],
        "coding_topic": "aggregation",
        "problem_type": "data processing",
        "difficulty": "Easy",
        "language": "python",
        "title": "Group Counts",
        "statement": (
            "Given a list of dictionaries, each containing a string field 'key', return a dictionary "
            "mapping each key to how many times it appears."
        ),
        "input": "rows: list[dict]",
        "output": "dict[str, int]",
        "constraints": "0 <= len(rows) <= 10^4",
        "function_name": "group_counts",
        "starter": "def group_counts(rows):\n    pass\n",
        "tests": [
            {"args": [[{"key": "a"}, {"key": "b"}, {"key": "a"}]], "expected": {"a": 2, "b": 1}},
            {"args": [[]], "expected": {}},
        ],
    },
    {
        "id": "normalize_path",
        "roles": ["devops_engineer", "cloud_engineer", "qa_engineer"],
        "coding_topic": "string processing",
        "problem_type": "utilities",
        "difficulty": "Easy",
        "language": "python",
        "title": "Normalize Unix Path",
        "statement": (
            "Simplify a Unix path. '.' means current directory, '..' means parent. "
            "Return the simplified canonical path starting with '/'."
        ),
        "input": "path: str",
        "output": "str",
        "constraints": "1 <= len(path) <= 3000",
        "function_name": "simplify_path",
        "starter": "def simplify_path(path):\n    pass\n",
        "tests": [
            {"args": ["/home/"], "expected": "/home"},
            {"args": ["/../"], "expected": "/"},
            {"args": ["/home//foo/"], "expected": "/home/foo"},
        ],
    },
]


def select_coding_problem(
    role_id: str,
    asked_problem_ids: Optional[List[str]] = None,
    difficulty: Optional[str] = None,
) -> Dict[str, Any]:
    asked = set(asked_problem_ids or [])
    candidates = [
        problem for problem in CODING_PROBLEMS
        if role_id in problem["roles"] and problem["id"] not in asked
    ]
    if difficulty:
        preferred = [p for p in candidates if p["difficulty"].lower() == difficulty.lower()]
        candidates = preferred or candidates
    if not candidates:
        candidates = [p for p in CODING_PROBLEMS if p["id"] not in asked] or CODING_PROBLEMS
    problem = dict(candidates[0])
    problem["test_cases"] = [
        {
            "input": test["args"],
            "output": test["expected"],
        }
        for test in problem["tests"]
    ]
    return {k: v for k, v in problem.items() if k != "tests"}


def get_coding_problem(problem_id: str) -> Optional[Dict[str, Any]]:
    """Return the internal problem definition, including executable tests."""
    for problem in CODING_PROBLEMS:
        if problem["id"] == problem_id:
            return dict(problem)
    return None


def public_problem_view(problem: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": problem.get("id"),
        "title": problem.get("title"),
        "coding_topic": problem.get("coding_topic"),
        "problem_type": problem.get("problem_type"),
        "difficulty": problem.get("difficulty"),
        "language": problem.get("language"),
        "statement": problem.get("statement"),
        "input": problem.get("input"),
        "output": problem.get("output"),
        "constraints": problem.get("constraints"),
        "starter": problem.get("starter"),
        "function_name": problem.get("function_name"),
        "test_cases": problem.get("test_cases") or [],
    }


def execute_submission(problem: Dict[str, Any], source_code: str) -> Dict[str, Any]:
    language = (problem.get("language") or "python").lower()
    if language != "python":
        return {
            "compiled": False,
            "execution_available": False,
            "missing_dependency": (
                "A multi-language sandbox such as Judge0 is not configured. "
                "Only Python execution is implemented locally."
            ),
            "passed": 0,
            "failed": 0,
            "total": len(problem.get("tests") or problem.get("test_cases") or []),
            "test_results": [],
            "runtime_error": None,
            "compile_error": None,
            **review_code(source_code, problem, passed_ratio=0.0),
        }

    tests = problem.get("tests")
    if not tests:
        tests = [
            {"args": case.get("input"), "expected": case.get("output")}
            for case in (problem.get("test_cases") or [])
        ]
    return _run_python(problem, source_code, tests)


def review_code(source_code: str, problem: Dict[str, Any], passed_ratio: float) -> Dict[str, Any]:
    code = source_code or ""
    lowered = code.lower()
    algorithm_quality = 3
    if "dict" in lowered or "set(" in lowered or "hash" in lowered:
        algorithm_quality = 7
    if "for " in lowered and "for " in lowered[lowered.find("for ") + 3:]:
        algorithm_quality = min(algorithm_quality, 5)
    if passed_ratio >= 1:
        algorithm_quality = max(algorithm_quality, 8)
    elif passed_ratio >= 0.5:
        algorithm_quality = max(algorithm_quality, 6)

    time_complexity = "Unknown"
    space_complexity = "Unknown"
    if "dict" in lowered or "set(" in lowered:
        time_complexity = "Likely O(n) with hash lookups"
        space_complexity = "O(n) auxiliary map/set"
    elif "for " in lowered:
        time_complexity = "At least O(n); nested loops may be O(n^2)"
        space_complexity = "O(1) extra unless additional structures are used"

    quality = 4
    if "def " in lowered:
        quality += 2
    if len(code.strip()) > 40:
        quality += 1
    if "pass" in lowered and passed_ratio == 0:
        quality = 2

    return {
        "algorithm_quality": min(10, algorithm_quality),
        "time_complexity": time_complexity,
        "space_complexity": space_complexity,
        "code_quality": min(10, quality),
        "coding_score": int(round(max(0, min(10, passed_ratio * 7 + algorithm_quality * 0.2 + quality * 0.1)))),
    }


def _run_python(problem: Dict[str, Any], source_code: str, tests: List[Dict[str, Any]]) -> Dict[str, Any]:
    function_name = problem.get("function_name") or "solve"
    runner = textwrap.dedent(
        f"""
        import json, sys
        USER_CODE = {source_code!r}
        TESTS = {json.dumps(tests)}
        FN = {function_name!r}
        ns = {{}}
        try:
            exec(USER_CODE, ns, ns)
        except Exception as exc:
            json.dump({{"compile_error": str(exc), "results": []}}, sys.stdout)
            raise SystemExit(0)
        if FN not in ns or not callable(ns[FN]):
            json.dump({{"compile_error": "Missing function " + FN, "results": []}}, sys.stdout)
            raise SystemExit(0)
        results = []
        for index, test in enumerate(TESTS):
            args = test.get("args") or []
            expected = test.get("expected")
            try:
                actual = ns[FN](*args) if isinstance(args, list) else ns[FN](args)
                passed = actual == expected
                results.append({{
                    "index": index,
                    "passed": passed,
                    "expected": expected,
                    "actual": actual,
                    "error": None,
                }})
            except Exception as exc:
                results.append({{
                    "index": index,
                    "passed": False,
                    "expected": expected,
                    "actual": None,
                    "error": str(exc),
                }})
        json.dump({{"compile_error": None, "results": results}}, sys.stdout)
        """
    )
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "runner.py"
        script.write_text(runner, encoding="utf-8")
        try:
            completed = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                timeout=6,
                cwd=tmp,
            )
        except subprocess.TimeoutExpired:
            return {
                "compiled": True,
                "execution_available": True,
                "passed": 0,
                "failed": len(tests),
                "total": len(tests),
                "test_results": [],
                "runtime_error": "Execution timed out after 6 seconds.",
                "compile_error": None,
                **review_code(source_code, problem, 0.0),
                "coding_score": 1,
            }

    payload: Dict[str, Any]
    try:
        payload = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"compile_error": completed.stderr or "Malformed runner output", "results": []}

    compile_error = payload.get("compile_error")
    results = payload.get("results") or []
    if compile_error:
        return {
            "compiled": False,
            "execution_available": True,
            "passed": 0,
            "failed": len(tests),
            "total": len(tests),
            "test_results": [],
            "runtime_error": None,
            "compile_error": compile_error,
            **review_code(source_code, problem, 0.0),
            "coding_score": 1,
        }

    passed = sum(1 for item in results if item.get("passed"))
    failed = len(results) - passed
    ratio = passed / max(1, len(results))
    review = review_code(source_code, problem, ratio)
    runtime_error = next((item.get("error") for item in results if item.get("error")), None)
    return {
        "compiled": True,
        "execution_available": True,
        "passed": passed,
        "failed": failed,
        "total": len(results),
        "test_results": results,
        "runtime_error": runtime_error,
        "compile_error": None,
        **review,
    }
