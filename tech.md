# SkinAid — Claude Context File

## Project Overview

**SkinAid** is a medical wound analysis system that uses computer vision and RAG to help users identify and get first-aid guidance for wounds and skin conditions from a photo.

- **Status:** ~80% refactored, targeting completion by early May
- **Architecture:** Modular Monolith (backend), with a separate AI/ML component

### Team

| Member | Role                            |
| ------ | ------------------------------- |
| Bình   | Backend (FastAPI, DB, API)      |
| Hiếu   | AI/ML (YOLO, EfficientNet)      |
| Tuấn   | Leader                          |
| Minh   | Frontend (React / React Native) |
| Nhàn   | Documentation                   |

---

## Core Workflow (Critical — Read First)

The main pipeline Claude must understand before touching any code:

```
B1: User uploads image (1 photo)
B2: User optionally edits/crops image
B3: AI(1) — YOLO checks if wound exists
    → No wound → B3.2: Display "no wound detected"
    → Wound found → continue to B4

B4: AI(2) — EfficientNet classifies:
    - Category: physical injury OR dermatological
    - Wound type (specific label)
    - Severity level (mild / moderate / severe)
    + DB lookup: maps AI result → first-aid suggestions

    → Display to user:
      - AI result (confidence, type, severity)
      - Questionnaire (specific to wound type)
      - First-aid suggestions from DB

B5: User answers questionnaire
    → RAG: retrieve relevant medical context (priority: DB → RAG → LLM)
    → LLM synthesizes response based on user's description

B6: Validate — compare LLM output vs DB
    → Different → B6.1: Show AI result + DB suggestions
    → Same     → B6.2: Show AI result + LLM suggestions

END
```

**Key pipeline rule:** DB is always the primary source of truth. RAG and LLM are secondary/fallback layers.

---

## Tech Stack

### Backend

- **Framework:** FastAPI
- **ORM:** SQLAlchemy + SQLModel
- **Validation:** Pydantic v2
- **Database:** PostgreSQL (relational) + Qdrant (vector DB)
- **Embeddings:** OpenAI embedding model
- **RAG:** LangChain + Qdrant + OpenAI embeddings (lives in `backend/app/modules/rag/`)
- **Auth:** JWT

### Frontend

- React (web) + React Native (mobile, in progress)
- JavaScript / TypeScript

### AI/ML (`ai_ml/` module)

- **Detection:** YOLO — detects presence and location of wound (12 categories)
- **Classification:** EfficientNet — severity classification (mild / moderate / severe)
- **Fallback:** Vision LLM (GPT-4.1) when EfficientNet confidence < 0.6

### Infrastructure

- Docker (local + production)
- Cloud deployment (TBD)

---

## Architecture

### Pattern: Modular Monolith

The backend is split into self-contained modules. Each module owns its own routes, services, repositories, and models.

```
backend/
├── app/                         ← application root
│   ├── api/                     ← route registration / API versioning
│   ├── core/                    ← shared config, DB session, security
│   ├── middleware/               ← FastAPI middleware (logging, auth checks...)
│   ├── modules/                 ← feature modules (each owns routes/service/repo/models)
│   │   ├── ai/                  ← orchestrator: calls ai_ml service via HTTP
│   │   ├── llm/                 ← LLM API integration (OpenAI, etc.)
│   │   ├── rag/                 ← RAG orchestration (Qdrant retrieval + LLM synthesis)
│   │   └── ...                  ← other business modules (auth, user, history, etc.)
│   ├── shared/                  ← shared utilities, base classes, exceptions
│   ├── __init__.py
│   └── main.py                  ← FastAPI app entry point
├── docs/                        ← API / technical documentation
├── migrations/                  ← Alembic migration files
├── scripts/                     ← utility scripts (seed data, etc.)
├── tests/                       ← test suite (pytest)
├── uploads/                     ← temporary uploaded image storage
├── .env / .env.example
├── alembic.ini
├── Dockerfile
└── requirements.txt

ai_ml/                           ← fully separate service, owns CV inference pipeline only
├── configs/                     ← model configs, hyperparameters
├── middleware/                  ← ai_ml-specific middleware
├── models/                      ← YOLO & EfficientNet model weights / loaders
├── pipeline/                    ← core pipeline logic (B3 → B4 orchestration)
├── routes/                      ← FastAPI routes exposed by ai_ml service
├── schemas/                     ← Pydantic schemas for AI input/output
├── utils/                       ← helper functions (image preprocessing, etc.)
├── .env / .env.example
├── main.py                      ← ai_ml service entry point
├── run.py
└── requirements.txt
```

### Module Placement Decision — RAG belongs in `backend`, NOT `ai_ml`

**Rule:** Separate ML inference (GPU/compute-heavy) from API orchestration (I/O-heavy).

| Module                     | Location  | Reason                                        |
| -------------------------- | --------- | --------------------------------------------- |
| `ai`                       | `backend` | Orchestrator — calls ai_ml service via HTTP   |
| `llm`                      | `backend` | Calls OpenAI/Gemini API — no model training   |
| `rag`                      | `backend` | Calls Qdrant + LLM API — no model training    |
| Detection / Classification | `ai_ml`   | Runs actual ML inference (YOLO, EfficientNet) |

**Why RAG is NOT in `ai_ml`:**

- RAG = retrieval orchestration (query Qdrant → retrieve chunks → prompt → call LLM API). This is I/O, not ML inference.
- RAG dependencies (`langchain`, `qdrant-client`, `openai`) are lightweight — should not be bundled with PyTorch/YOLO in `ai_ml`.
- `ai_ml` should be scalable independently on GPU instances. RAG + backend scales on CPU.
- Consistent with `llm` module already living in `backend`.

**Only move RAG to `ai_ml` if:**

- You need to fine-tune a custom embedding model
- You need to train a custom retriever model (not using Qdrant + OpenAI off-the-shelf)

### `rag` Module Internal Structure

```
backend/app/modules/rag/
├── router.py          ← FastAPI routes (called by ai/ module after B4)
├── service.py         ← RAG orchestration logic (retrieve → synthesize)
├── retriever.py       ← Qdrant vector search with wound_type metadata filter
├── chains.py          ← LangChain LCEL chains
├── schemas.py         ← Pydantic request/response models
└── document/          ← Medical knowledge base documents (indexed into Qdrant)
```

### Repository Pattern (within each module)

```
Router (Controller) → Service → Repository → SQLAlchemy ORM → PostgreSQL
```

**Critical rules:**

- `Repository`: only calls `session.flush()` — never `session.commit()`
- `Service`: owns the transaction boundary, calls `session.commit()`
- Never commit inside a repository method

### Coding Conventions

- Language: Python, follows **PEP 8**
- Naming: `snake_case` for files, functions, variables
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Follow Clean Architecture principles where possible (domain logic stays in service layer, not routes or repos)
- Pydantic v2 schemas for all request/response models

---

## Key Technical Decisions

1. **YOLO first, EfficientNet second** — always run detection before classification. Never skip B3.
2. **Confidence threshold = 0.6** — if EfficientNet confidence < 0.6, trigger GPT-4.1 Vision as fallback verifier.
3. **DB → RAG → LLM priority** — DB suggestions always shown first. RAG/LLM only used when DB has no match or for synthesis (B5).
4. **Qdrant for RAG** — vector search over medical knowledge base. Metadata filtering by `wound_type` before semantic search.
5. **SQLModel + SQLAlchemy** — SQLModel for schema definition, SQLAlchemy for session management and queries.
6. **Modular Monolith over microservices** — team size and deadline make microservices unnecessary overhead.
7. **RAG lives in `backend`, not `ai_ml`** — RAG is API orchestration (Qdrant + LLM), not ML inference. Keeps `ai_ml` focused on GPU-bound compute only. See Module Placement Decision above.

