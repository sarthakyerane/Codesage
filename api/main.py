"""
CodeSage FastAPI Application Entry Point
AI-powered multi-language code analysis via RAG + static analysis + LLM.
"""
import os
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from models.schemas import HealthResponse
from services import metadata_store, vector_store, llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 CodeSage starting up...")
    # Initialize MySQL pool and ChromaDB on startup
    try:
        await metadata_store.get_pool()
        logger.info("MySQL pool ready ✓")
    except Exception as e:
        logger.error(f"MySQL connection failed: {e}")
    vector_store._get_collection()
    logger.info("ChromaDB ready ✓")
    logger.info(f"Active LLM: {llm.get_active_model()}")
    logger.info("✅ CodeSage is ready! Visit http://localhost:8000/docs")
    yield
    # Cleanup on shutdown
    await metadata_store.close_pool()
    logger.info("CodeSage shutdown complete.")


app = FastAPI(
    title="CodeSage",
    description="""
## 🧠 CodeSage: AI-powered Code Analysis

Upload code in any supported language and ask AI to:
- **Debug** memory leaks, segfaults, logic errors, wrong outputs
- **Generate** unit tests automatically (Catch2 / Google Test)
- **Explain** algorithm complexity and control flow

### LLM Priority
Groq (`llama-3.3-70b-versatile`) → OpenAI (`gpt-4o`) → Ollama (`deepseek-coder:6.7b`)

### Quick Start
1. `POST /upload_code` — Upload any supported source file
2. `POST /debug_function` — Ask "Fix memory leak in Dijkstra"
3. `POST /generate_tests` — Get unit tests for any function
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Allow frontend / Swagger to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ─────────────────────────────────────────────────────────
from routers import upload, debug, tests

app.include_router(upload.router)
app.include_router(debug.router)
app.include_router(tests.router)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Check that all services are online and connected."""
    mysql_ok = await metadata_store.ping()
    chroma_count = vector_store.get_collection_count()
    ollama_ok = await llm.ping_ollama()

    return HealthResponse(
        status="ok",
        mysql="connected" if mysql_ok else "❌ disconnected",
        chromadb=f"connected ({chroma_count} functions indexed)",
        ollama=f"connected ({llm.get_active_model()})" if ollama_ok else "❌ disconnected — run: ollama serve",
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@app.get("/", tags=["System"])
async def root():
    return {
        "name": "CodeSage",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "upload": "POST /upload_code",
            "debug": "POST /debug_function",
            "tests": "POST /generate_tests",
        },
    }

# v1.0 - production ready
