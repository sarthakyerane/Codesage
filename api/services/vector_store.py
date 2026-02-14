"""
ChromaDB vector store service.
Stores C++ function embeddings and provides semantic search.
"""
import os
import uuid
from loguru import logger
import chromadb
from chromadb.config import Settings

_client = None
_collection = None
COLLECTION_NAME = "cpp_functions"


def _get_collection():
    global _client, _collection
    if _collection is None:
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "/app/chroma_db")
        logger.info(f"Initializing ChromaDB at: {persist_dir}")
        _client = chromadb.PersistentClient(path=persist_dir)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # cosine similarity for code embeddings
        )
        logger.info(f"ChromaDB collection '{COLLECTION_NAME}' ready ✓")
    return _collection


def upsert_function(
    chroma_id: str,
    embedding: list[float],
    document: str,
    function_name: str,
    file_path: str,
    complexity: int,
    tags: str,
    line_start: int,
    line_end: int,
) -> str:
    """
    Insert or update a function's embedding in ChromaDB.
    Returns the chroma_id used.
    """
    collection = _get_collection()
    collection.upsert(
        ids=[chroma_id],
        embeddings=[embedding],
        documents=[document],
        metadatas=[{
            "function_name": function_name,
            "file_path": file_path,
            "complexity": complexity,
            "tags": tags,
            "line_start": line_start,
            "line_end": line_end,
        }],
    )
    return chroma_id


def query_similar(
    query_embedding: list[float],
    top_k: int = 5,
    file_filter: str | None = None,
) -> list[dict]:
    """
    Search for the most similar function embeddings.
    
    Args:
        query_embedding: Embedding of the user's query
        top_k: Number of results to return
        file_filter: Optional file name to restrict search to
        
    Returns:
        List of dicts with document, metadata, and distance
    """
    collection = _get_collection()

    where = None
    if file_filter:
        where = {"file_path": {"$eq": file_filter}}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count() or 1),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    if results and results["ids"]:
        for i, doc_id in enumerate(results["ids"][0]):
            hits.append({
                "id": doc_id,
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })
    return hits


def delete_by_file(file_path: str) -> int:
    """Delete all embeddings for a given file. Returns count deleted."""
    collection = _get_collection()
    results = collection.get(where={"file_path": {"$eq": file_path}})
    ids = results.get("ids", [])
    if ids:
        collection.delete(ids=ids)
    return len(ids)


def get_collection_count() -> int:
    """Return total number of indexed functions."""
    return _get_collection().count()


def generate_chroma_id(file_path: str, function_name: str) -> str:
    """Generate a stable, unique ID for a function."""
    return f"{file_path}::{function_name}"
