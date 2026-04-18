# ============================================================
# backend/Dockerfile — SkinAid Backend Service
# ============================================================
# Base: python:3.11-slim
# ⚠️  Image size sẽ ~4-5 GB do torch + opencv + tesseract
# ============================================================
FROM python:3.11-slim AS base

# ── System dependencies ────────────────────────────────────
# libglib2.0-0 libgl1 libgomp1 : opencv + torch
# tesseract-ocr                 : pytesseract (OCR)
# poppler-utils                 : pdf2image (PDF → image)
# libpq-dev                     : psycopg2 (PostgreSQL C driver)
# curl                          : health check
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgl1 \
        libgomp1 \
        libgthread-2.0-0 \
        tesseract-ocr \
        poppler-utils \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user ─────────────────────────────────────────
RUN groupadd -r skinaid && useradd -r -g skinaid skinaid

WORKDIR /app

# ── Install Python dependencies (cache layer) ─────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Copy application source ───────────────────────────────
COPY --chown=skinaid:skinaid . .

# ── Create runtime directories ────────────────────────────
RUN mkdir -p uploads logs models models_backup models_temp rag_docs \
    && chown -R skinaid:skinaid uploads logs models models_backup models_temp rag_docs

# ── Switch to non-root ────────────────────────────────────
USER skinaid

# ── Environment defaults ───────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# ── Health check ──────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Start command ─────────────────────────────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]