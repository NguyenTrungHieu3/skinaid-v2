# Stage 1: Build
FROM node:20-alpine AS builder

# Build argument cho API URL
ARG VITE_API_URL=http://localhost:8000/api/v1
ENV VITE_API_URL=$VITE_API_URL

# Thiết lập working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Cài đặt dependencies
RUN npm ci --legacy-peer-deps

# Copy source code
COPY . .

# Build ứng dụng (Vite output ra thư mục 'dist')
RUN npm run build

# Stage 2: Production với Nginx
FROM nginx:alpine

# Copy file cấu hình nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build output từ stage builder (Vite output là 'dist')
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Lệnh để Nginx chạy
CMD ["nginx", "-g", "daemon off;"]