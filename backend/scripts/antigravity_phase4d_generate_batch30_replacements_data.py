"""Batch 30 Replacements (AI Engineer)."""

ROLE = "AI Engineer"

BUCKET_KEYS = {
    "AI_EVALUATION": ("AI Evaluation", "Model Benchmarking", "LLMs", ["AI Engineer", "Machine Learning Engineer", "Data Scientist"]),
    "STRUCTURED_OUTPUTS": ("Structured Outputs", "Data Extraction", "LLMs", ["AI Engineer", "Data Engineer", "Backend Developer"]),
}

Q = [
("AI_EVALUATION", "scenario", "medium", "scenario", ["LLM-as-a-judge", "Bias"],
 "You run an automated benchmark to compare two generation models. Model A uses simple vocabulary and gets high human ratings. Model B uses complex academic words but gets lower human ratings. However, your automated 'LLM-as-a-judge' gives Model B a much higher score. What bias is the judge exhibiting?",
 "This is 'Vocabulary Bias' or 'Complexity Bias'. The evaluator LLM is inherently biased towards highly formal, complex, or academic language, confusing stylistic complexity with actual reasoning quality or factual correctness. To fix this, the judge's grading rubric must explicitly decouple tone and vocabulary style from the evaluation of factual correctness.",
 ["'Vocabulary Bias' or 'Complexity Bias'", "The evaluator LLM falsely equates complex/academic language with higher quality", "Fix: The grading rubric must explicitly decouple tone/style from factual correctness"],
 ["The LLM judge prefers Model B because they are from the same server farm"]),

("STRUCTURED_OUTPUTS", "implement", "medium", "implementation", ["JSON Schema", "Nullability"],
 "You use an LLM to extract data into a specific JSON schema. The schema requires `person_age` to be an integer. The LLM often outputs `{\"person_age\": \"unknown\"}` when it cannot find the age, crashing the strict JSON parser. How do you alter the JSON schema definition to safely handle this?",
 "You must make the field nullable by defining the type as an array of allowed types (e.g., `type: [\"integer\", \"null\"]`) or using `anyOf`. By allowing the schema to explicitly accept a `null` value when the integer is unidentifiable, the LLM can safely communicate missing data without violating the strict type constraints or resorting to strings.",
 ["Make the field explicitly nullable in the schema definition", "Define the type as an array (e.g., `type: [\"integer\", \"null\"]`)", "Allows the LLM to safely communicate missing data without violating integer type constraints"],
 ["Change the database to accept 'unknown' as a valid math integer"])
]
