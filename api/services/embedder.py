"""
Embedding service using Ollama.
Converts code text into dense vector representations for semantic search.
Uses the 'nomic-embed-text' model by default.
"""
import os
import httpx
from loguru import logger

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
EMBED_MODEL_NAME = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")


def embed_text(text: str) -> list[float]:
    """
    Embed a single text string using Ollama.
    """
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json={
                    "model": EMBED_MODEL_NAME,
                    "prompt": text,
                }
            )
            response.raise_for_status()
            return response.json()["embedding"]
    except Exception as e:
        logger.error(f"Ollama embedding error: {e}")
        raise RuntimeError(f"Failed to get embeddings from Ollama. model: {EMBED_MODEL_NAME}, error: {e}")


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed multiple texts. Since Ollama's /api/embeddings is usually single-prompt,
    we loop through them or use a batch model if supported.
    """
    embeddings = []
    for text in texts:
        embeddings.append(embed_text(text))
    return embeddings


def build_function_document(function_name: str, return_type: str,
                             parameters: str, body: str, tags: list[str]) -> str:
    """
    Build a rich text representation of a function for embedding.
    We include the signature + tags + body so the vector captures
    both what the function IS and what it DOES.
    """
    tag_str = ", ".join(tags) if tags else "general"
    doc = f"""
Function: {function_name}
Signature: {return_type} {function_name}({parameters})
Tags: {tag_str}
Code:
{body}
""".strip()
    return doc
