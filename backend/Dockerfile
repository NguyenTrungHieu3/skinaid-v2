# ================================================================
# SkinAid Backend — Optimized Dockerfile
# ================================================================
FROM python:3.11-slim

WORKDIR /app

# ── 1. System deps ───────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        curl \
        libglib2.0-0 \
        libmagic1 \
        tesseract-ocr \
        poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ── 2. Pip upgrade ───────────────────────────────────────────────
RUN pip install --no-cache-dir --upgrade pip

# ── 3. PyTorch CPU — layer riêng để Docker cache khi rebuild ────
# Giữ 2.8.0 theo yêu cầu — cần EC2 ít nhất 20GB disk
RUN pip install --no-cache-dir \
        torch==2.8.0 \
        torchvision==0.23.0 \
        torchaudio==2.8.0 \
        --index-url https://download.pytorch.org/whl/cpu \
    && find /usr/local/lib/python3.11/site-packages/torch -name "test" -type d -exec rm -rf {} + 2>/dev/null || true

# ── 4. Các thư viện còn lại ──────────────────────────────────────
# pywin32 và win32_setctime tự động bỏ qua trên Linux nhờ platform marker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip cache purge

# ── 5. Source code ───────────────────────────────────────────────
COPY . .

# ── 6. Thư mục uploads ──────────────────────────────────────────
RUN mkdir -p /app/uploads/guest /app/uploads/user \
    && chmod -R 755 /app/uploads

# ── 7. Non-root user ─────────────────────────────────────────────
RUN adduser --disabled-password --gecos '' --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# ── 8. Environment ───────────────────────────────────────────────
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FASTEMBED_CACHE_DIR=/app/.cache/fastembed

EXPOSE $PORT

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]