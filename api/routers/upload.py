"""
Upload Router: POST /upload_code
Accepts source files in any supported language (C++, Python, JS, Java, Go, Rust, etc.).
Parses functions via tree-sitter, embeds with Ollama, and stores in ChromaDB + MySQL.
"""
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from loguru import logger
from models.schemas import UploadResponse
from services import embedder, vector_store, metadata_store
from services.parser import (
    get_parser_instance, get_language_from_filename, SUPPORTED_EXTENSIONS
)

router = APIRouter(prefix="/upload_code", tags=["Upload"])
_parser = get_parser_instance()

# Track the most recently uploaded file for auto-scoping debug queries
last_uploaded_file: str | None = None


@router.post("", response_model=UploadResponse)
async def upload_code(file: UploadFile = File(...)):
    """
    Upload a source file in any supported language. The API will:
    1. Parse all functions using tree-sitter (regex fallback if tree-sitter unavailable)
    2. Embed each function using Ollama (nomic-embed-text)
    3. Store embeddings in ChromaDB for semantic search
    4. Store metadata (file path, function names, line numbers, complexity) in MySQL

    Re-uploading the same file replaces all existing data for that file.
    Returns a summary of what was indexed and the detected call graph.
    """
    # ── Validate file type ────────────────────────────────────────────
    ext = ""
    for e in SUPPORTED_EXTENSIONS:
        if file.filename.lower().endswith(e):
            ext = e
            break
    if not ext:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: '{file.filename}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )
        )

    _, display_lang = get_language_from_filename(file.filename)

    source_bytes = await file.read()
    source_code = source_bytes.decode("utf-8", errors="replace")
    file_path = f"/uploads/{file.filename}"  # Virtual path for storage
    
    # Track last uploaded file for auto-scoping debug queries
    global last_uploaded_file
    last_uploaded_file = file_path

    logger.info(f"Processing upload: {file.filename} ({len(source_bytes)} bytes)")

    # ── Parse source code ─────────────────────────────────────────────
    functions = _parser.parse_file(source_code, file_path=file.filename)
    if not functions:
        raise HTTPException(
            status_code=422,
            detail=f"No functions found in the uploaded {display_lang} file. "
                   "Make sure it contains valid function definitions."
        )

    call_graph = _parser.build_call_graph(functions)
    logger.info(f"Parsed {len(functions)} functions from {file.filename}")

    # ── Store file metadata in MySQL ──────────────────────────────────
    file_id = await metadata_store.upsert_file(
        file_path=file_path,
        file_name=file.filename,
        function_count=len(functions),
    )

    # ── Delete old embeddings for this file (re-upload case) ─────────
    vector_store.delete_by_file(file_path)
    await metadata_store.delete_functions_by_file(file_id)

    # ── Embed + store each function ───────────────────────────────────
    documents = []
    chroma_ids = []
    embeddings_batch = []
    metadatas = []
    fn_records = []

    for fn in functions:
        doc = embedder.build_function_document(
            function_name=fn.name,
            return_type=fn.return_type,
            parameters=fn.parameters,
            body=fn.body,
            tags=fn.tags,
        )
        chroma_id = vector_store.generate_chroma_id(file_path, fn.name)
        documents.append(doc)
        chroma_ids.append(chroma_id)
        metadatas.append({
            "function_name": fn.name,
            "file_path": file_path,
            "complexity": fn.complexity,
            "tags": ",".join(fn.tags),
            "line_start": fn.line_start,
            "line_end": fn.line_end,
        })
        fn_records.append(fn)

    # Batch embed for speed
    embeddings_batch = embedder.embed_batch(documents)

    # Batch upsert into ChromaDB
    collection = vector_store._get_collection()
    collection.upsert(
        ids=chroma_ids,
        embeddings=embeddings_batch,
        documents=documents,
        metadatas=metadatas,
    )

    # Store each function in MySQL + call edges
    for i, fn in enumerate(fn_records):
        fn_id = await metadata_store.insert_function(
            file_id=file_id,
            function_name=fn.name,
            return_type=fn.return_type,
            parameters=fn.parameters,
            line_start=fn.line_start,
            line_end=fn.line_end,
            complexity=fn.complexity,
            tags=fn.tags,
            chroma_id=chroma_ids[i],
            body_preview=fn.body,
        )
        await metadata_store.insert_call_edges(fn_id, fn.calls)

    logger.info(f"Successfully indexed {len(functions)} functions from {file.filename}")

    return UploadResponse(
        file_id=file_id,
        file_name=file.filename,
        functions_indexed=len(functions),
        call_graph=call_graph,
        message=f"✅ Successfully indexed {len(functions)} {display_lang} functions. "
                f"You can now query: POST /debug_function or /generate_tests",
    )
