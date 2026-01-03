# 🧠 CodeSage

> AI-powered code analysis tool using RAG (Retrieval-Augmented Generation).

---

## Purpose

CodeSage lets developers upload source code and ask questions about it in plain English. Instead of pasting your entire codebase into ChatGPT, CodeSage:

- **Parses** your code into individual functions using tree-sitter AST
- **Embeds** each function as a semantic vector for RAG retrieval
- **Analyzes** C/C++ code with a native static analyzer for deterministic bug detection
- **Generates** complete unit tests and suggested fixes in any supported language

---

## Tech Stack

| Layer | Technology | Role |
|---|---|---|
| **API** | FastAPI (Python) | REST endpoints, async, Swagger docs |
| **Parsing** | tree-sitter | Multi-language AST parsing (10+ languages) |
| **Static Analysis** | Custom C++ analyzer | Detects memory leaks, buffer overflows, resource leaks |
| **Embeddings** | Ollama + nomic-embed-text | 768-dim semantic vectors (runs locally) |
| **Vector DB** | ChromaDB | Cosine similarity search |
| **Metadata DB** | MySQL 8.0 | File/function metadata and call graph |
| **LLM** | Groq → OpenAI → Ollama | Priority fallback chain for code analysis |
| **Cache** | Redis 7 | Session and result caching |
| **Infra** | Docker Compose | One-command setup |

---

## LLM Priority Chain

CodeSage automatically selects the best available LLM at startup:

1. **Groq** (`llama-3.3-70b-versatile`) — fast cloud inference, free tier available
2. **Ollama** (`deepseek-coder:6.7b`) — fully local fallback, no API key needed

The active model is shown in the `/health` endpoint and startup logs.

---

## How It Works

```
UPLOAD → tree-sitter Parser → Extract Functions → Embed → ChromaDB + MySQL

DEBUG  → Embed Query → Semantic Search → C/C++ Analyzer (if .c/.cpp)
              → Combine Code + Findings → LLM → Fix + Explanation
```

---

## C/C++ Static Analyzer

CodeSage includes a native C++ binary (`analyzer/analyzer.cpp`) that performs deterministic bug detection on C and C++ files:

- **Memory leaks** — `new` without `delete`
- **Buffer overflows** — unsafe `gets()`, `strcpy()`
- **Resource leaks** — `fopen()` without `fclose()`

The analyzer runs automatically on C/C++ uploads and during debug queries when a C/C++ file is scoped. Its JSON findings are injected directly into the LLM prompt — hybrid static analysis + AI.

For non-C/C++ files, the analyzer is skipped (these bug classes don't apply to garbage-collected languages).

---

## Supported Languages

C++ · C · Python · JavaScript · TypeScript · JSX · TSX · Java · Go · Rust · Ruby · PHP

**File extensions:** `.cpp`, `.cc`, `.cxx`, `.c`, `.h`, `.hpp`, `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.java`, `.go`, `.rs`, `.rb`, `.php`

---

## Quick Start

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) + [Ollama](https://ollama.com)

```bash
# 1. Pull embedding model (required — used for all languages)
ollama pull nomic-embed-text
ollama serve

# 2. Configure environment
cp .env.example .env
# Edit .env and add your Groq API key (free at console.groq.com)
# Or add OPENAI_API_KEY, or leave both blank to use Ollama locally

# 3. Start all services
docker-compose up --build
```

Open → **http://localhost:8000/docs**

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | _(empty)_ | Groq API key — enables cloud LLM (recommended) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model to use |
| `OPENAI_API_KEY` | _(empty)_ | OpenAI key — fallback if no Groq key |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama server URL |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model (always required) |
| `OLLAMA_MODEL` | `deepseek-coder:6.7b` | Local LLM fallback model |
| `MYSQL_HOST` | `mysql` | MySQL hostname |
| `MYSQL_PORT` | `3306` | MySQL port |
| `MYSQL_DATABASE` | `codesage` | Database name |
| `MYSQL_USER` | `codesage_user` | Database user |
| `MYSQL_PASSWORD` | `codesage_pass` | Database password |
| `CHROMA_PERSIST_DIR` | `/app/chroma_db` | ChromaDB persistence directory |
| `REDIS_URL` | `redis://redis:6379` | Redis connection URL |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## API

| Endpoint | Method | Description |
|---|---|---|
| `/upload_code` | POST | Upload any supported source file for indexing |
| `/debug_function` | POST | Describe a bug in natural language → get a fix |
| `/generate_tests` | POST | Generate unit tests for a named function |
| `/health` | GET | Service health status (MySQL, ChromaDB, Ollama) |
| `/` | GET | API info and available endpoints |

### POST `/upload_code`

Accepts any supported language file. Parses all functions via tree-sitter, embeds them with Ollama, and stores everything in ChromaDB + MySQL. Re-uploading a file replaces existing data.

**Response includes:** `file_id`, `file_name`, `functions_indexed`, `call_graph`, `message`

### POST `/debug_function`

```json
{
  "query": "Fix memory leak in my Dijkstra implementation",
  "file_filter": "/uploads/graph.cpp",
  "top_k": 5
}
```

- `query` — natural language bug description (required)
- `file_filter` — optional; auto-scopes to last uploaded file if omitted
- `top_k` — number of code chunks to retrieve (1–20, default 5)

**Response includes:** `query`, `retrieved_functions`, `suggested_fix`, `explanation`, `static_analysis_findings`

### POST `/generate_tests`

```json
{
  "function_name": "dijkstra",
  "framework": "catch2"
}
```

- `function_name` — name of the function to test (required)
- `framework` — `"catch2"` (default) or `"gtest"`

**Response includes:** `function_name`, `unit_tests_code`, `framework`, `explanation`

---

## Database Schema

Three tables in MySQL:

- **`files`** — uploaded file metadata (`file_path`, `file_name`, `function_count`, `upload_time`)
- **`functions`** — parsed function details (`function_name`, `return_type`, `parameters`, `line_start`, `line_end`, `complexity`, `tags`, `chroma_id`, `body_preview`)
- **`call_edges`** — call graph edges (`caller_id` → `callee_name`)

---

## Project Structure

```
codesage/
├── docker-compose.yml
├── .env.example
├── mysql/
│   └── init.sql                # Database schema + init
├── analyzer/
│   ├── analyzer.cpp            # C/C++ static analyzer (outputs JSON)
│   └── Makefile
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # FastAPI app, lifespan, health check
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   ├── routers/
│   │   ├── upload.py           # POST /upload_code
│   │   ├── debug.py            # POST /debug_function
│   │   └── tests.py            # POST /generate_tests
│   └── services/
│       ├── parser.py           # tree-sitter multi-lang parser + regex fallback
│       ├── embedder.py         # Ollama embeddings (nomic-embed-text)
│       ├── vector_store.py     # ChromaDB (cosine similarity)
│       ├── metadata_store.py   # MySQL async (aiomysql)
│       ├── rag.py              # RAG pipeline + LLM prompts
│       ├── analyzer.py         # C/C++ analyzer subprocess wrapper
│       └── llm.py              # LLM client (Groq → OpenAI → Ollama fallback)
└── sample_cpp/                 # Example C++ files for testing
```

---

## License

MIT
