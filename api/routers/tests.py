"""
Tests Router: POST /generate_tests
Generates unit tests for a named C++ function using RAG + LLM.
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from models.schemas import GenerateTestsRequest, GenerateTestsResponse
from services import rag, vector_store

router = APIRouter(prefix="/generate_tests", tags=["Tests"])


@router.post("", response_model=GenerateTestsResponse)
async def generate_tests(request: GenerateTestsRequest):
    """
    Generate unit tests for a C++ function.
    
    Examples:
    - {"function_name": "dijkstra", "framework": "catch2"}
    - {"function_name": "mergeSort", "framework": "gtest"}
    
    The API will:
    1. Find the function and its callees in ChromaDB
    2. Pass the full context to the LLM
    3. Return complete, compilable unit tests
    
    Supported frameworks: 'catch2' (default), 'gtest'
    """
    if vector_store.get_collection_count() == 0:
        raise HTTPException(
            status_code=400,
            detail="No code indexed yet. Upload a .cpp file first: POST /upload_code"
        )

    if request.framework not in ("catch2", "gtest"):
        raise HTTPException(
            status_code=400,
            detail="Invalid framework. Use 'catch2' or 'gtest'"
        )

    logger.info(f"Generate tests: '{request.function_name}' ({request.framework})")

    try:
        result = rag.answer_generate_tests(
            function_name=request.function_name,
            framework=request.framework,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return GenerateTestsResponse(**result)
