# 🧠 CodeSage

> AI-powered code analysis tool using RAG (Retrieval-Augmented Generation).

---

## Purpose

CodeSage lets developers upload source code and ask questions about it in plain English. Instead of pasting your entire codebase into ChatGPT, CodeSage:

- **Parses** your code into individual functions using tree-sitter AST
- **Embeds** each function as a semantic vector
- **Retrieves** only the most relevant functions for your query
- **Analyzes** C++ code with a static analyzer for deterministic bug detection
- **Sends** focused context + findings to an LLM for accurate fixes

---

## Tech Stack

| Layer | Technology | Role |
|---|---|---|
| **API** | FastAPI (Python) | REST endpoints, async, Swagger docs |
| **Parsing** | tree-sitter | Multi-language AST parsing (10+ languages) |
| **Static Analysis** | Custom C++ analyzer | Detects memory leaks, buffer overflows, resource leaks |
| **Embeddings** | Ollama + nomic-embed-text | 768-dim semantic vectors |
| **Vector DB** | ChromaDB | Cosine similarity search |
| **Metadata DB** | MySQL | File/function metadata and call graph |
| **LLM** | Groq (llama-3.3-70b) | Cloud inference for code analysis |
| **Infra** | Docker Compose | One-command setup |

---

## How It Works

```
UPLOAD → tree-sitter Parser → Extract Functions → Embed → ChromaDB + MySQL

DEBUG  → Embed Query → Semantic Search → C++ Analyzer (if .cpp)
              → Combine Code + Findings → LLM → Fix + Explanation
```

---

## C++ Static Analyzer

CodeSage includes a native C++ binary (`analyzer/analyzer.cpp`) that performs deterministic bug detection on C++ files:

- **Memory leaks** — `new` without `delete`
- **Buffer overflows** — unsafe `gets()`, `strcpy()`
- **Resource leaks** — `fopen()` without `fclose()`

The analyzer runs automatically on C++ uploads. Its findings are injected into the LLM prompt so the AI has both code context and confirmed bugs — hybrid static analysis + AI.

For non-C++ files, the analyzer is skipped (these bug classes don't exist in garbage-collected languages).

---

## Supported Languages

C++ · C · Python · JavaScript · TypeScript · Java · Go · Rust · Ruby · PHP

---

## Quick Start

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) + [Ollama](https://ollama.com)

```bash
# 1. Pull embedding model
ollama pull nomic-embed-text
ollama serve

# 2. Configure
cp .env.example .env
# Add your Groq API key (free at console.groq.com)

# 3. Start
docker-compose up --build
```

Open → **http://localhost:8000/docs**

---

## API

| Endpoint | Method | Description |
|---|---|---|
| `/upload_code` | POST | Upload source file for indexing |
| `/debug_function` | POST | Describe a bug → get a fix |
| `/generate_tests` | POST | Generate unit tests for a function |
| `/health` | GET | Service health status |

---

## Project Structure

```
codesage/
├── docker-compose.yml
├── .env.example
├── mysql/init.sql
├── analyzer/
│   ├── analyzer.cpp            # C++ static analyzer
│   └── Makefile
├── api/
│   ├── main.py
│   ├── models/schemas.py
│   ├── routers/
│   │   ├── upload.py
│   │   ├── debug.py
│   │   └── tests.py
│   └── services/
│       ├── parser.py           # tree-sitter multi-lang parser
│       ├── embedder.py         # Ollama embeddings
│       ├── vector_store.py     # ChromaDB
│       ├── metadata_store.py   # MySQL
│       ├── rag.py              # RAG pipeline
│       ├── analyzer.py         # C++ analyzer wrapper
│       └── llm.py              # LLM client (Groq/OpenAI/Ollama)
└── sample_cpp/
```

---

## License

MIT
