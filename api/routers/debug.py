"""
Debug Router: POST /debug_function
Takes a natural language bug description, retrieves relevant code via RAG,
returns a fix + explanation from the LLM.
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from models.schemas import DebugRequest, DebugResponse
from services import rag, vector_store
from services.analyzer import analyze_file, is_analyzable

router = APIRouter(prefix="/debug_function", tags=["Debug"])


@router.post("", response_model=DebugResponse)
async def debug_function(request: DebugRequest):
    """
    Describe a bug in natural language.
    
    Examples:
    - "Fix memory leak in my Dijkstra implementation"
    - "My BFS returns wrong shortest path"
    - "Segfault when graph has no edges"
    
    The API will:
    1. Embed your query semantically
    2. Find the most relevant functions in your codebase
    3. Run C++ static analyzer if applicable
    4. Send code + findings to the LLM with a Chain-of-Thought debugging prompt
    5. Return the fixed code + explanation
    """
    if vector_store.get_collection_count() == 0:
        raise HTTPException(
            status_code=400,
            detail="No code indexed yet. Upload a file first: POST /upload_code"
        )

    # Auto-scope to last uploaded file if no file_filter provided
    file_filter = request.file_filter
    if not file_filter:
        from routers.upload import last_uploaded_file
        if last_uploaded_file:
            file_filter = last_uploaded_file
            logger.info(f"Auto-scoping to last uploaded file: {file_filter}")

    logger.info(f"Debug query: '{request.query}' (top_k={request.top_k}, file={file_filter})")

    # Run static analyzer if we have a C++ file filter
    analyzer_findings = []
    if file_filter and is_analyzable(file_filter):
        try:
            import aiofiles, os
            file_path = file_filter
            if os.path.exists(file_path):
                async with aiofiles.open(file_path, 'r') as f:
                    source_code = await f.read()
                analyzer_findings = await analyze_file(file_path, source_code)
                logger.info(f"Static analyzer found {len(analyzer_findings)} issue(s)")
        except Exception as e:
            logger.warning(f"Static analyzer skipped: {e}")

    try:
        result = rag.answer_debug(
            query=request.query,
            top_k=request.top_k,
            file_filter=file_filter,
            analyzer_findings=analyzer_findings,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return DebugResponse(**result)
