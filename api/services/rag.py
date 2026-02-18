"""
RAG pipeline - retrieves relevant code from ChromaDB and uses LLM for answers.
"""
import re
from loguru import logger
from services import embedder, vector_store, llm
from services.analyzer import format_findings_for_prompt

DEBUG_PROMPT = """You are an expert {language} engineer.

A developer asked: "{query}"

Relevant {language} functions from their codebase:

{code_chunks}

{static_analysis}

Instructions:
1. Check static analysis findings first (if any) - these are confirmed issues.
2. Identify any additional bugs.
3. Provide corrected code as a complete function.
4. Explain what was wrong and why.

## Root Cause
[bug explanation]

## Fixed Code
```{lang_tag}
[corrected function]
```

## Explanation
[why this fix works]
"""

TEST_PROMPT = """Generate unit tests for this {language} code using {framework}:

{code_chunks}

Cover normal cases, edge cases, and error conditions.
Output ONLY the test code:

```{lang_tag}
[tests here]
```
"""

LANG_MAP = {
    "python": ("Python", "python"), "javascript": ("JavaScript", "javascript"),
    "typescript": ("TypeScript", "typescript"), "java": ("Java", "java"),
    "go": ("Go", "go"), "rust": ("Rust", "rust"), "ruby": ("Ruby", "ruby"),
    "php": ("PHP", "php"),
}

FRAMEWORK_NAMES = {
    "catch2": "Catch2", "gtest": "Google Test", "pytest": "pytest",
    "jest": "Jest", "junit": "JUnit 5",
}


def _detect_language(hits):
    counts = {}
    for hit in hits:
        tags = hit.get("metadata", {}).get("tags", "")
        for lang in LANG_MAP:
            if lang in tags:
                counts[lang] = counts.get(lang, 0) + 1
    if counts:
        top = max(counts, key=counts.get)
        return LANG_MAP[top]
    return "C++", "cpp"


def retrieve(query, top_k=5, file_filter=None):
    query_embedding = embedder.embed_text(query)
    hits = vector_store.query_similar(query_embedding, top_k=top_k, file_filter=file_filter)
    logger.info(f"Retrieved {len(hits)} chunks for: '{query[:50]}'")
    return hits


def format_chunks(hits):
    if not hits: return "No relevant code found."
    parts = []
    for i, hit in enumerate(hits, 1):
        meta = hit.get("metadata", {})
        name = meta.get("function_name", "?")
        sim = 1 - hit.get("distance", 1)
        parts.append(f"--- [{i}] {name} (similarity: {sim:.2f}) ---\n{hit['document']}")
    return "\n\n".join(parts)


def answer_debug(query, top_k=5, file_filter=None, analyzer_findings=None):
    hits = retrieve(query, top_k, file_filter)
    chunks = format_chunks(hits)
    lang, tag = _detect_language(hits)
    static = format_findings_for_prompt(analyzer_findings or [])

    prompt = DEBUG_PROMPT.format(
        query=query, code_chunks=chunks, language=lang,
        lang_tag=tag, static_analysis=static,
    )
    logger.info(f"LLM call ({llm.get_active_model()}) for debug [{lang}]")
    response = llm.generate(prompt, temperature=0.1)
    fix = _extract_code(response)
    explanation = response.split("## Explanation", 1)[-1].strip() if "## Explanation" in response else response

    return {
        "query": query,
        "retrieved_functions": [h.get("metadata", {}).get("function_name", "?") for h in hits],
        "suggested_fix": fix,
        "explanation": explanation,
        "static_analysis_findings": len(analyzer_findings or []),
    }


def answer_generate_tests(function_name, framework="catch2", top_k=3):
    hits = retrieve(function_name, top_k=top_k)
    chunks = format_chunks(hits)
    lang, tag = _detect_language(hits)
    fw_name = FRAMEWORK_NAMES.get(framework, framework)

    prompt = TEST_PROMPT.format(code_chunks=chunks, framework=fw_name, language=lang, lang_tag=tag)
    logger.info(f"Generating {fw_name} tests for {function_name}")
    response = llm.generate(prompt, temperature=0.2)
    code = _extract_code(response)

    return {
        "function_name": function_name,
        "unit_tests_code": code or response,
        "framework": framework,
        "explanation": f"Generated {fw_name} tests for `{function_name}` ({lang}).",
    }


def _extract_code(text):
    m = re.search(r'```[\w+]*\n(.*?)```', text, re.DOTALL)
    return m.group(1).strip() if m else ""
