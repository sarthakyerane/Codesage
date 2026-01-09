"""
Pydantic schemas for CodeSage request/response models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UploadResponse(BaseModel):
    file_id: int
    file_name: str
    functions_indexed: int
    call_graph: dict[str, List[str]]
    message: str


class DebugRequest(BaseModel):
    query: str = Field(..., description="Describe the bug or issue, e.g. 'Fix memory leak in Dijkstra'")
    file_filter: Optional[str] = Field(None, description="Optional: filter search to a specific file name")
    top_k: int = Field(5, ge=1, le=20, description="Number of code chunks to retrieve")


class DebugResponse(BaseModel):
    query: str
    retrieved_functions: List[str]
    suggested_fix: str
    explanation: str
    static_analysis_findings: int = Field(0, description="Number of bugs found by C++ static analyzer")


class GenerateTestsRequest(BaseModel):
    function_name: str = Field(..., description="Name of the function to generate tests for")
    file_id: Optional[int] = Field(None, description="Optional: restrict to a specific file")
    framework: str = Field("catch2", description="Test framework: 'catch2' or 'gtest'")


class GenerateTestsResponse(BaseModel):
    function_name: str
    unit_tests_code: str
    framework: str
    explanation: str


class FunctionInfo(BaseModel):
    id: int
    function_name: str
    file_path: str
    line_start: int
    line_end: int
    complexity: int
    tags: Optional[str]


class HealthResponse(BaseModel):
    status: str
    mysql: str
    chromadb: str
    ollama: str
    timestamp: str
