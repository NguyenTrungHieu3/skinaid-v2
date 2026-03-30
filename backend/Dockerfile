# Sử dụng parent image python:3.11-slim
FROM python:3.13-slim

# Thiết lập working directory
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    curl \
    libglib2.0-0 \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy file requirements_flexible.txt vào trong image
COPY requirements_flexible.txt .

# Cài đặt các thư viện Python cần thiết
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements_flexible.txt

# Copy source code
COPY . .

# Tạo thư mục uploads và cấp quyền
RUN mkdir -p /app/uploads/guest /app/uploads/user \
    && chmod -R 755 /app/uploads

# Tạo user non-root để chạy ứng dụng (bảo mật)
RUN adduser --disabled-password --gecos '' --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Khai báo thông tin port
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
