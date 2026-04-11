# ============================================================
# frontend/Dockerfile — SkinAid Frontend (Multi-stage)
# ============================================================
# Stage 1: Build React app với Vite
# Stage 2: Serve static files với nginx:alpine
# Final image size: ~30 MB (chỉ nginx + built files)
# ============================================================

# ─────────────────────────────────────────────────────────
# Stage 1: Builder
# ─────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first → npm ci → cache hiệu quả
COPY package.json package-lock.json ./
RUN npm ci --prefer-offline

# Copy source code
COPY . .

# Build args → trở thành VITE_ env vars lúc build
# Truyền vào khi docker build:
#   --build-arg VITE_API_URL=https://yourdomain.com/api/v1
#   --build-arg VITE_BACKEND_URL=https://yourdomain.com
ARG VITE_API_URL
ARG VITE_BACKEND_URL
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL

# Vite build → output ra /app/dist
RUN npm run build

# ─────────────────────────────────────────────────────────
# Stage 2: Serve
# ─────────────────────────────────────────────────────────
FROM nginx:1.27-alpine AS serve

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config (SPA routing + proxy /api)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Non-root: nginx chạy bằng user nginx (mặc định trong nginx:alpine)
# Port 80 → cần quyền bind, dùng nginx:alpine đã config sẵn

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:80/ > /dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]