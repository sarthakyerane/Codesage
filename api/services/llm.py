"""
LLM client - auto-selects: Groq -> OpenAI -> Ollama (local fallback).
"""
import os
from loguru import logger

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-coder:6.7b")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

SYS_MSG = "You are an expert software engineer with deep knowledge of data structures, algorithms, and debugging."


def generate(prompt, temperature=0.2, max_tokens=2048):
    if GROQ_KEY.strip():
        return _call_groq(prompt, temperature, max_tokens)
    if OPENAI_KEY.strip():
        return _call_openai(prompt, temperature, max_tokens)
    return _call_ollama(prompt, temperature, max_tokens)


def _call_groq(prompt, temp, max_tok):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=GROQ_KEY, base_url="https://api.groq.com/openai/v1")
        r = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": SYS_MSG}, {"role": "user", "content": prompt}],
            temperature=temp, max_tokens=max_tok,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq error: {e}")
        raise RuntimeError(f"Groq failed: {e}")


def _call_ollama(prompt, temp, max_tok):
    try:
        import ollama
        client = ollama.Client(host=OLLAMA_URL)
        r = client.generate(model=OLLAMA_MODEL, prompt=prompt, options={"temperature": temp, "num_predict": max_tok})
        return r.get("response", "").strip()
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        raise RuntimeError(f"Ollama failed. Is it running? Error: {e}")


def _call_openai(prompt, temp, max_tok):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
        r = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": SYS_MSG}, {"role": "user", "content": prompt}],
            temperature=temp, max_tokens=max_tok,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        raise RuntimeError(f"OpenAI failed: {e}")


def get_active_model():
    if GROQ_KEY.strip(): return f"groq/{GROQ_MODEL}"
    if OPENAI_KEY.strip(): return "openai/gpt-4o"
    return f"ollama/{OLLAMA_MODEL}"


async def ping_ollama():
    import httpx
    try:
        async with httpx.AsyncClient(timeout=3.0) as c:
            return (await c.get(f"{OLLAMA_URL}/api/tags")).status_code == 200
    except Exception:
        return False
