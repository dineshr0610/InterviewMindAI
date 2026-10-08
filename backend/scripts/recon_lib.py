"""
LOCAL / READ-ONLY analysis library for the InterviewMind question-bank reconstruction audit.

Nothing in here touches the database, Gemini, or any network resource. It operates on a
local JSON snapshot of public.document_embeddings (id, content, metadata, has_embedding).

Design rules (per audit brief):
  * One extractor PER SOURCE FORMAT - no single generic regex.
  * Question wording is PRESERVED. Only markup wrappers (HTML tags/entities) are removed;
    `question_raw` always keeps the original characters so fidelity can be verified.
  * Nothing is generated, paraphrased or "repaired".
"""
from __future__ import annotations

import html
import re
from collections import Counter

# --------------------------------------------------------------------------------------
# Source identification
# --------------------------------------------------------------------------------------
SOURCE_RULES = [
    ("codealpaca", "CodeAlpaca"),
    ("InterviewMind", "Curated-v1"),
    ("javascript-interview", "JavaScript"),
    ("reactjs-interview", "React"),
    ("system-design-primer", "SystemDesign"),
    ("/aws/", "DevOps-AWS"),
    ("/kubernetes/", "DevOps-K8s"),
    ("/linux/", "DevOps-Linux"),
    ("/git/", "DevOps-Git"),
    ("/cicd/", "DevOps-CICD"),
]
DEVOPS_SOURCES = {"DevOps-AWS", "DevOps-K8s", "DevOps-Linux", "DevOps-Git", "DevOps-CICD"}
DEVOPS_SKILL = {"DevOps-AWS": "AWS", "DevOps-K8s": "Kubernetes", "DevOps-Linux": "Linux",
                "DevOps-Git": "Git", "DevOps-CICD": "CI/CD"}


def source_of(meta) -> str:
    s = (meta or {}).get("source") or ""
    for needle, name in SOURCE_RULES:
        if needle in s:
            return name
    return "UNSOURCED"


# --------------------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------------------
_HTML_TAGS = (r"b|i|u|em|strong|code|br|p|a|span|div|pre|ul|ol|li|h[1-6]|details|summary|img|hr|sub|"
              r"sup|kbd|table|tr|td|th|thead|tbody|blockquote")
_TAG_RE = re.compile(rf"(?i)</?(?:{_HTML_TAGS})\b[^>]*>")


def html_to_text(s: str) -> str:
    """Remove ONLY known HTML wrapper tags + unescape entities; keep all words/backticks verbatim."""
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = _TAG_RE.sub("", s)
    s = html.unescape(s).replace("\r", "")
    out = []
    for ln in (x.strip() for x in s.split("\n")):
        if ln == "" and (not out or out[-1] == ""):
            continue
        out.append(ln)
    return "\n".join(out).strip()


def norm_for_dedupe(s: str) -> str:
    s = html_to_text(s).lower()
    s = re.sub(r"^\s*(?:#+\s*)?(?:\d+[\.\)]\s*)", "", s)
    s = re.sub(r"[`*_#>\[\]()]", " ", s)
    s = re.sub(r"[^a-z0-9+#./ -]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tokens(s: str) -> frozenset:
    return frozenset(t for t in norm_for_dedupe(s).split() if len(t) > 1)


def jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def has_mojibake(s: str) -> bool:
    return "\ufffd" in s


# --------------------------------------------------------------------------------------
# Row splitting for the "### Technical Interview Question:" rendering (JS / React / DevOps / SD)
# --------------------------------------------------------------------------------------
_BODY_SPLIT = re.compile(r"####\s*Technical Explanation\s*&\s*Model Answer\s*\n")


def split_tiq_row(content: str):
    """Return (header_text, body_text) for rows rendered by parse_numbered_markdown_qa()."""
    first, _, rest = content.partition("\n")
    header = first.split(":", 1)[1].strip() if ":" in first else first.strip()
    m = _BODY_SPLIT.search(rest)
    body = rest[m.end():] if m else rest
    return header, body


_ANSWER_NOISE = [
    re.compile(r"\*\*\[.{0,3}Back to Top\]\(#[^)]*\)\*\*"),
    re.compile(r"(?m)^\s*---\s*$"),
    re.compile(r"(?i)</?(?:p|details)>"),
    re.compile(r"(?m)^\s*\d+\.\s*$"),  # dangling "59." numbering that belongs to the NEXT question
]


def clean_answer(body: str) -> str:
    t = body
    for rx in _ANSWER_NOISE:
        t = rx.sub("", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


# --------------------------------------------------------------------------------------
# Question-form detection
# --------------------------------------------------------------------------------------
INTERROG = re.compile(
    r"^(what|how|why|when|which|where|who|whom|whose|explain|describe|can|could|does|do|did|is|are|was|"
    r"were|will|would|should|shall|list|name|define|compare|differentiate|distinguish|give|write|tell|"
    r"state|mention|difference|differences|enumerate|elaborate|discuss|illustrate|demonstrate|outline|"
    r"identify|justify|in what|under what|if|suppose|imagine|assume|create|implement|design|build|"
    r"convert|find|determine|is it|are there|have you|has|have)\b", re.I)

CODE_OUTPUT_RE = re.compile(
    r"(what('| i)?s? (is|are|will be|would be) the (output|result)|output of (the )?(below|following|given|above)|"
    r"what (is|will) (printed|logged|displayed)|what happens (when|if) (you )?(run|execute)|"
    r"what does (the )?(below|following|above) (code|snippet|program))", re.I)

CONTEXT_DEP_RE = re.compile(
    r"\b(below|above|following|given|this|these|the (code|snippet|example|diagram|image|picture|screenshot|figure))\b"
    r".{0,25}\b(code|snippet|example|diagram|image|picture|screenshot|figure|table|output|program|function|"
    r"yaml|manifest|file|command|script)\b", re.I)

HANDS_ON_VERBS = (
    "create|delete|run|write|show|deploy|scale|change|modify|add|remove|update|label|apply|expose|set|"
    "configure|install|build|use|make|launch|start|stop|restart|kill|mount|copy|move|find|display|print|"
    "fetch|verify|retrieve|rename|edit|patch|execute|setup|assign|attach|detach|connect|login|log in|"
    "clone|commit|push|pull|checkout|merge|rebase|tag|stash|revert|reset|squash|cherry-pick|schedule|"
    "taint|drain|cordon|rollout|rollback|upgrade|downgrade|enable|disable|mark|annotate|tail|grep|sort")
HANDS_ON_RE = re.compile(rf"^(?:{HANDS_ON_VERBS})\b", re.I)
SCENARIO_RE = re.compile(r"^(you|your|suppose|imagine|assume|given|consider|if you|when you|a (user|customer|team|developer|company)|an? (application|app|service|pod|cluster|server|website))\b", re.I)
COMPARE_RE = re.compile(r"\b(differen(ce|t|ces|tiate)|compare|comparison|distinguish|versus|vs\.?)\b", re.I)
VISUAL_RE = re.compile(r"(place the components|fill in the (blanks|missing)|in the right placeholders|following (diagram|image|picture|screenshot|figure)|<img\b|!\[)", re.I)


def classify_qtype(q: str, *, raw: str = "") -> str:
    t = q.strip()
    t = re.sub(r"^\s*(?:#+\s*)?\d+[\.\)]\s*", "", t)
    if VISUAL_RE.search(raw or t):
        return "needs_visual"
    if re.match(r"(?i)^true or false", t):
        return "true_false"
    if CODE_OUTPUT_RE.search(t):
        return "code_output_quiz"
    if re.match(r"(?i)^design\b", t):
        return "design_prompt"
    if SCENARIO_RE.match(t) and not HANDS_ON_RE.match(t):
        return "scenario"
    if HANDS_ON_RE.match(t) and not re.match(r"(?i)^(show me how|use cases?)\b", t):
        return "hands_on_task"
    if COMPARE_RE.search(t):
        return "compare"
    if re.match(r"(?i)^how\b", t):
        return "how_to"
    if INTERROG.match(t) or t.endswith("?"):
        return "concept"
    return "unknown_form"


CONVERSATIONAL_TYPES = {"concept", "compare", "how_to", "scenario", "design_prompt"}


# --------------------------------------------------------------------------------------
# JS / React  (one DB row == one "### N. Question" section, body is the model answer)
# --------------------------------------------------------------------------------------
def classify_tiq_header(h: str) -> str:
    """
    Returns one of:
      question | code_output_quiz | fragment_answer_key | fragment_subheading | noun_heading
    A header starting with '#' means the ingestion regex captured an H1/H2 that lives INSIDE an
    answer (e.g. '# Syntax', '## Answer: 3') and promoted it to a fake question.
    """
    t = h.strip()
    if CODE_OUTPUT_RE.search(t):
        return "code_output_quiz"
    if re.match(r"^#{1,6}\s*answer\b", t, re.I):
        return "fragment_answer_key"
    if t.startswith("#") or t.startswith("**"):
        return "fragment_subheading"
    t2 = re.sub(r"^\d+[\.\)]\s*", "", t)
    if INTERROG.match(t2) or t2.endswith("?"):
        return "question"
    return "noun_heading"


# --------------------------------------------------------------------------------------
# DevOps  (one DB row == one README section containing MANY <details><summary>Q</summary>A</details>)
# --------------------------------------------------------------------------------------
_SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>", re.S | re.I)
_DETAILS_END_RE = re.compile(r"(?i)</details>|<details>")


def extract_devops_items(body: str):
    items = []
    for m in _SUMMARY_RE.finditer(body):
        raw = m.group(1)
        start = m.end()
        nxt = _DETAILS_END_RE.search(body, start)
        closed = bool(nxt and nxt.group(0).lower() == "</details>")
        ans_raw = body[start:nxt.start()] if nxt else body[start:]
        items.append({"question_raw": raw, "answer_raw": ans_raw, "closed": closed})
    return items


# --------------------------------------------------------------------------------------
# System Design Primer  (headings = documentation; interview prompts live in markdown tables)
# --------------------------------------------------------------------------------------
SD_LIST_ROW_SUBTOPICS = {
    "system design interview questions with solutions",
    "object-oriented design interview questions with solutions",
    "additional system design interview questions",
}


def extract_sd_table_questions(body: str):
    qs = []
    for ln in body.split("\n"):
        ln = ln.strip()
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if not cells:
            continue
        c0 = cells[0]
        if not c0 or set(c0) <= set("-: ") or c0.lower() == "question":
            continue
        if re.match(r"(?i)^add (an? )?.*question$", c0):
            continue
        qs.append(c0)
    return qs


# --------------------------------------------------------------------------------------
# CodeAlpaca
# --------------------------------------------------------------------------------------
CA_WRITE = re.compile(r"^(write|create|implement|design|develop|generate|construct|build|make|code|program|produce|compose|define|devise|come up|formulate|using|use)\b", re.I)
CA_MODIFY = re.compile(r"^(edit|fix|modify|update|change|rewrite|refactor|debug|correct|optimi[sz]e|improve|complete|replace|add|remove|insert|rearrange|adapt|extend|alter|convert|translate|transform|port|reformat|simplify|rework|revise|amend)\b", re.I)
CA_EXPLAIN = re.compile(r"^(explain|describe|discuss|compare|what|why|how|summari[sz]e|outline|identify|name|list|state|differentiate|elaborate|classify|analy[sz]e|evaluate|is|are|does|can|which|tell)\b", re.I)
CA_CODE_READ = re.compile(r"(output of|what (is|will) (the )?(output|result)|what does (this|the) (code|function|program)|predict the output|trace)", re.I)
CA_TASK = re.compile(r"^(find|calculate|compute|sort|count|print|output|take|given|check|determine|return|reverse|sum|display|select|extract|parse|read|get|merge|combine|filter|iterate|loop|generate|select|perform|apply|insert|convert|swap|multiply|divide|subtract|remove|delete|search|replace|split|join|concatenate|round|execute|run|set|assign|declare|initiali[sz]e|call|invoke|access|store|pass|round|rotate|shuffle|validate|verify|reorder|order|group|sum up|add up)\b", re.I)

LANG_PATTERNS = [
    ("python", r"\bpython\b|\bdef \w+\(|\bimport (numpy|pandas|os|sys|re|math|random)\b|\bprint\("),
    ("java", r"\bjava\b(?!script)|public (static )?(class|void)|system\.out"),
    ("javascript", r"\bjavascript\b|\bjs\b|console\.log|\bconst \w+ =|=>\s*[\{\(]|\bnode(\.js)?\b|\bjquery\b"),
    ("typescript", r"\btypescript\b"),
    ("sql", r"\bsql\b|\bselect\b.+\bfrom\b|\bmysql\b|\bpostgres|\bsqlite\b"),
    ("c++", r"c\+\+|#include|\bcout\b|\bstd::"),
    ("c#", r"\bc#|\bcsharp\b|\.net\b"),
    ("c", r"\bin c\b|\ba c (program|function|code)\b|\bprintf\("),
    ("html/css", r"\bhtml\b|\bcss\b|<div|<html|\bdom\b"),
    ("bash", r"\bbash\b|\bshell\b|\bsh script\b|#!/bin"),
    ("ruby", r"\bruby\b"),
    ("php", r"\bphp\b"),
    ("go", r"\bgolang\b|\bin go\b|\bgo (program|function)\b"),
    ("r", r"\bin r\b|\br (program|script|code|language)\b"),
    ("swift", r"\bswift\b"),
    ("kotlin", r"\bkotlin\b"),
    ("rust", r"\brust\b"),
    ("perl", r"\bperl\b"),
    ("matlab", r"\bmatlab\b"),
    ("scala", r"\bscala\b"),
]


def detect_language(instruction: str, code: str = "") -> str:
    low_i = instruction.lower()
    for name, pat in LANG_PATTERNS:
        if re.search(pat, low_i):
            return name
    low_c = code.lower()
    for name, pat in LANG_PATTERNS:
        if re.search(pat, low_c):
            return name
    return "unspecified"


def parse_codealpaca(content: str):
    first, _, rest = content.partition("\n")
    instruction = first.split(":", 1)[1].strip() if ":" in first else first.strip()
    desc = re.search(r"#### Problem Description\n(.*?)(?=\n#### Verified Solution)", rest, re.S)
    inp = re.search(r"\*\*Input Specification\*\*:\n```\n(.*?)\n```", rest, re.S)
    sol = re.search(r"#### Verified Solution & Code Implementation\n```[a-z]*\n(.*?)\n```", rest, re.S)
    return {
        "instruction": instruction,
        "problem_description": (desc.group(1).strip() if desc else ""),
        "input_spec": (inp.group(1).strip() if inp else ""),
        "reference_output": (sol.group(1).strip() if sol else ""),
    }


def classify_ca_instruction(instr: str) -> str:
    t = instr.strip()
    if CA_CODE_READ.search(t):
        return "code_reading"
    if CA_MODIFY.match(t):
        return "modify_code"
    if CA_WRITE.match(t):
        return "write_code"
    if CA_TASK.match(t):
        return "coding_task_verb"
    if CA_EXPLAIN.match(t):
        return "conceptual_instruction"
    return "other"


def first_word(s: str) -> str:
    m = re.match(r"\s*([A-Za-z\-']+)", s)
    return m.group(1).lower() if m else ""


# --------------------------------------------------------------------------------------
# Curated-v1 (generator output) classification
# --------------------------------------------------------------------------------------
QUESTION_TEMPLATE_RE = re.compile(
    r"^Explain how .+ operates in the context of .+\. What are the primary trade-offs when choosing this "
    r"approach over standard alternatives in .+ applications\?$", re.S)


def classify_curated(content: str) -> str:
    c = content
    if "**Question**:" in c and "**Ideal Model Answer" in c:
        return "template_interview_question"
    if "#### Architectural Overview" in c:
        return "template_core_concept_deep_dive"
    if c.startswith("### Production Scenario"):
        return "template_production_scenario"
    if c.startswith("### Code Implementation"):
        return "template_code_pattern"
    if c.startswith("### Pitfalls & Best Practices"):
        return "template_pitfalls_checklist"
    return "other_curated"


def balanced_parens(s: str) -> bool:
    return s.count("(") == s.count(")")


# --------------------------------------------------------------------------------------
# Heuristic skill/topic keyword rules (PROPOSED - heuristic, not source-derived)
# --------------------------------------------------------------------------------------
JS_TOPICS = [
    ("async_programming", r"promise|async|await|callback|settimeout|setinterval|event loop|microtask|asynchronous|race condition|generator|thenable"),
    ("closures_scope", r"closure|scope|hoist|lexical|iife|immediately invoked|temporal dead|\btdz\b|\bvar\b|\blet\b|\bconst\b"),
    ("functions", r"function|currying|higher.order|arrow|\bbind\b|\bcall\b|\bapply\b|recursion|memoiz|pure|default param|rest param|spread|decorator"),
    ("objects_prototypes_oop", r"prototype|inherit|\bclass\b|constructor|\bobject\b|\bthis\b|\bnew\b|getter|setter|freeze|seal|mixin|singleton|property|symbol|encapsulat"),
    ("types_coercion_equality", r"typeof|\bnull\b|undefined|\bnan\b|coercion|equality|===|==|truthy|falsy|primitive|bigint|\bnumber\b|\bstring\b|boolean|\bjson\b|\bdate\b|infinity"),
    ("arrays_collections", r"\barray|\bmap\b|\bset\b|weakmap|weakset|slice|splice|filter|reduce|foreach|\bsort\b|flat|destructur|iterat|\bloop\b|collection"),
    ("es6_modules_syntax", r"module|\bimport\b|\bexport\b|commonjs|es6|es2015|template literal|optional chaining|nullish|strict mode|ecmascript|\bproxy\b|reflect"),
    ("dom_events_browser", r"\bdom\b|\bevent|bubbl|captur|delegation|preventdefault|\bwindow\b|\bdocument\b|cookie|localstorage|sessionstorage|indexeddb|web worker|service worker|\bhistory\b|\bfetch\b|\bxhr\b|\bajax\b|\bcors\b|websocket|browser|\burl\b|\bhtml\b|\bcss\b"),
    ("error_handling_debugging", r"\berror|exception|try.{0,20}catch|debug|\bconsole\b|finally|\bthrow"),
    ("performance_security", r"performance|debounce|throttl|lazy|memory|garbage|\bxss\b|\bcsrf\b|security|sanitiz|\bcsp\b|\beval\b|optimi"),
]
REACT_TOPICS = [
    ("hooks", r"\bhooks?\b|usestate|useeffect|usememo|usecallback|useref|usecontext|usereducer|uselayouteffect|usetransition|usedeferredvalue|useid|useimperativehandle|useevent"),
    ("state_management", r"redux|\bflux\b|\bcontext\b|\bstore\b|reducer|\baction|mobx|zustand|recoil|state management|prop drilling|thunk|saga|selector"),
    ("rendering_vdom", r"virtual dom|reconcil|fiber|\brender|diffing|createelement|cloneelement|shadow dom|batch|strict ?mode|concurrent|\bjsx\b|\bkeys?\b"),
    ("components_props_state", r"component|\bprops?\b|\bstate\b|lifecycle|componentdid|controlled|uncontrolled|stateless|stateful|pure component|children|fragment|render prop|higher.order|\bhoc\b|composition|default props|proptypes"),
    ("routing", r"router|\broutes?\b|navigat|browserrouter|useparams|\blink\b"),
    ("forms_events", r"\bform|\bevents?\b|synthetic|onchange|\binput\b|\brefs?\b"),
    ("performance", r"\bmemo\b|\blazy\b|suspense|code splitting|optimi|performance|profil|virtualiz|windowing"),
    ("testing_tooling", r"\btest|\bjest\b|enzyme|testing library|eslint|babel|webpack|create react app|\bcra\b|\bvite\b|storybook"),
    ("styling", r"\bstyl|\bcss\b|styled|tailwind|inline"),
    ("advanced_patterns", r"portal|error boundar|\bssr\b|server.side|hydrat|next\.?js|server component|forwardref"),
    ("react_native_ecosystem", r"react native|ecosystem|library|libraries"),
]


def multi_topics(text: str, rules) -> list:
    low = text.lower()
    return [name for name, pat in rules if re.search(pat, low)]


# Application "domain" category keyword rules (to evaluate deterministic assignability)
CATEGORY_RULES = {
    "database_design": r"\bsql\b|database|\bindex(es|ing)?\b|transaction|schema|\bquery\b|nosql|rdbms|\bacid\b|sharding|replication|\bdb\b",
    "api_design": r"\bapi\b|\brest(ful)?\b|\bhttp|endpoint|graphql|\brpc\b|status code|webhook",
    "security_auth": r"security|\bauth|oauth|\bjwt\b|\bxss\b|\bcsrf\b|encrypt|\biam\b|permission|\btls\b|\bssl\b|secret|\brbac\b|\bcors\b|sanitiz|\bcsp\b|vulnerab",
    "performance_scalability": r"performance|scal(e|ing|ability)|cach(e|ing)|latency|throughput|load balanc|optimi|memoiz|\blazy\b|debounce|throttl|bottleneck",
    "debugging_edge_cases": r"debug|troubleshoot|\berror|\bfail|exception|crash|not working|\bbug\b|edge case|race condition",
    "architecture": r"architect|microservice|monolith|\bdesign\b|component|pattern|high.level|\bcdn\b|sharding|replication|federation",
    "trade_offs": r"trade-?off|pros and cons|advantages?|disadvantages?|drawbacks?|benefits?|versus|\bvs\b|differen(ce|t)",
    "implementation": r"\bimplement|\bcreate|\bbuild|\bwrite|how (to|do|can|would) (you )?(use|create|implement|write|build|configure|set)",
}
