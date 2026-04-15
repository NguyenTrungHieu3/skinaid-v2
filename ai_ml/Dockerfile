# ============================================================
# ai_ml/Dockerfile — SkinAid AI Service
# ============================================================
# Base: python:3.11-slim (torch+opencv cần glibc, không dùng alpine)
# ⚠️  Image size sẽ ~3-4 GB do torch+torchvision+model weights
# ============================================================
FROM python:3.11-slim AS base

# ── System dependencies ────────────────────────────────────
# libglib2.0-0   : required by opencv-python
# libgomp1       : required by torch (OpenMP)
# libgl1         : required by opencv-python (libGL.so.1)
# libgthread-2.0-0: required by opencv
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgomp1 \
        libgl1 \
        libgthread-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user ─────────────────────────────────────────
RUN groupadd -r skinaid && useradd -r -g skinaid skinaid

WORKDIR /app

# ── Install Python dependencies (cache layer) ─────────────
# Copy requirements first → pip install → then copy source
# Khi code thay đổi, layer pip install vẫn được cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Copy source code ──────────────────────────────────────
COPY --chown=skinaid:skinaid . .

# ── Model weights ─────────────────────────────────────────
# Model files được COPY vào image (nặng ~150MB)
# Alternative: mount qua Docker volume nếu muốn update model không rebuild image
# COPY --chown=skinaid:skinaid models/ models/

# ── Switch to non-root ────────────────────────────────────
USER skinaid

# ── Environment defaults ───────────────────────────────────
ENV API_HOST=0.0.0.0 \
    API_PORT=8001 \
    RELOAD=false \
    WORKERS=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8001

# ── Health check ──────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

# ── Start command ─────────────────────────────────────────
# Dùng shell form để nhận biến môi trường API_HOST/API_PORT
CMD ["sh", "-c", "uvicorn main:app --host $API_HOST --port $API_PORT --workers $WORKERS"]