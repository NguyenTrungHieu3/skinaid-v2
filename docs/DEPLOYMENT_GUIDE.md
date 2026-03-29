# AI Model Management System - Deployment Guide (PBI-27)

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Backend Setup](#backend-setup)
4. [AI/ML Service Setup](#aiml-service-setup)
5. [Frontend Setup](#frontend-setup)
6. [Database Migration](#database-migration)
7. [Configuration](#configuration)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Monitoring & Maintenance](#monitoring--maintenance)
11. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers deployment of the AI Model Management System (PBI-27), which provides:
- Model upload with validation (500MB limit, multiple formats)
- Version control and lifecycle management
- Hot reload capability for runtime model switching
- Comprehensive audit trail
- Admin dashboard for model management

### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend    │────▶│  AI/ML Svc  │
│  (React)    │     │  (FastAPI)   │     │  (Python)   │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  PostgreSQL  │
                    └──────────────┘
```

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows 10+
- **CPU**: 4+ cores (8+ recommended for AI/ML)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 50GB+ for model files
- **GPU**: Optional (NVIDIA with CUDA for AI inference acceleration)

### Software Requirements

- **Python**: 3.9+
- **Node.js**: 18+
- **PostgreSQL**: 14+
- **Docker**: 20+ (optional, for containerized deployment)

---

## Backend Setup

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/skinaid

# Security
SECRET_KEY=your-secret-key-at-least-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Service
AI_SERVICE_URL=http://localhost:8001
AI_API_KEY=your-ai-api-key

# Model Upload
MODEL_UPLOAD_MAX_SIZE=524288000  # 500MB
MODEL_UPLOAD_ALLOWED_EXTENSIONS=.pt,.pth,.h5,.onnx,.safetensors
MODEL_STORAGE_DIR=./models
MODEL_STORAGE_BACKUP_DIR=./models_backup
```

### 3. Create Storage Directories

```bash
mkdir -p models models_backup models_temp
```

### 4. Run Backend

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## AI/ML Service Setup

### 1. Install Dependencies

```bash
cd ai_ml
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Note:** Requirements include:
- `ultralytics` (YOLO)
- `torch` (PyTorch)
- `timm` (EfficientNet)
- `opencv-python`
- `fastapi`
- `uvicorn`

### 2. Configure Environment

Create `.env` file:

```bash
# Model Paths
YOLO_MODEL_PATH=./models/detection/yolo_model.pt
EFFICIENTNET_MODEL_PATH=./models/classification/efficientnet_model.pth

# Device
EFFICIENTNET_DEVICE=cpu  # or cuda

# API
AI_API_KEY=your-ai-api-key
```

### 3. Place Model Files

```bash
# Create directories
mkdir -p models/detection models/classification

# Copy your trained models
cp /path/to/yolo.pt models/detection/
cp /path/to/efficientnet.pth models/classification/
```

### 4. Register Model Reload Router

In `ai_ml/main.py`, add:

```python
from routes.model_reload import router as reload_router

app.include_router(reload_router)
```

### 5. Run AI/ML Service

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

---

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env` file:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 3. Add Translations

Merge the model management translations into your locale files:

```bash
# Copy from locale files created during implementation
cat src/locales/model_management_en.json >> src/locales/en.json
cat src/locales/model_management_vi.json >> src/locales/vi.json
```

### 4. Run Frontend

```bash
npm run dev
```

Access at: `http://localhost:5173`

---

## Database Migration

### 1. Create Tables

The system uses SQLModel with these new tables:

- `ai_models`: Model storage with versioning
- `model_version_history`: Version change history
- `model_audit_logs`: Audit trail
- `model_performance`: Performance metrics

### 2. Run Migrations

If using Alembic:

```bash
cd backend
alembic revision --autogenerate -m "Add model management tables"
alembic upgrade head
```

Or create tables programmatically:

```python
from sqlmodel import SQLModel, create_engine
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SQLModel.metadata.create_all(engine)
```

---

## Configuration

### Environment Variables

#### Backend (.env)

```bash
# Model Upload Settings
MODEL_UPLOAD_MAX_SIZE=524288000        # 500MB in bytes
MODEL_UPLOAD_MIN_SIZE=1024             # 1KB minimum
MODEL_UPLOAD_ALLOWED_EXTENSIONS=.pt,.pth,.h5,.onnx,.safetensors
MODEL_UPLOAD_ALLOWED_TYPES=detection,classification,segmentation,severity_scoring
MODEL_STORAGE_DIR=models
MODEL_STORAGE_BACKUP_DIR=models_backup
MODEL_STORAGE_TEMP_DIR=models_temp
MODEL_HASH_ALGORITHM=sha256
MODEL_VALIDATE_ON_UPLOAD=true
MODEL_AUTO_ACTIVATE_ON_UPLOAD=false
```

#### AI/ML Service (.env)

```bash
# Model Reload Settings
AI_API_KEY=your-secure-api-key
RELOAD_LOCK_ENABLED=true
MAX_RELOAD_RETRIES=3
```

### Security

1. **Change Default API Keys**: Generate secure random keys
2. **Enable HTTPS**: Use SSL/TLS in production
3. **CORS Configuration**: Restrict to allowed origins
4. **Rate Limiting**: Configure per endpoint

---

## Testing

### Backend Tests

```bash
cd backend
pytest tests/test_model_validator.py -v
pytest tests/ -k "model" -v
```

### Frontend Tests

```bash
cd frontend
npm test
npm run lint
npm run build
```

### Integration Testing

1. **Upload Test**: Upload a valid model file
2. **Activation Test**: Activate uploaded model
3. **Rollback Test**: Rollback to previous version
4. **Reload Test**: Trigger runtime reload
5. **Audit Test**: Verify audit logs are created

---

## Deployment

### Docker Deployment (Recommended)

#### 1. Build Images

```bash
docker-compose build
```

#### 2. Start Services

```bash
docker-compose up -d
```

#### 3. Check Status

```bash
docker-compose ps
docker-compose logs -f
```

### Production Deployment

#### 1. Backend (Gunicorn)

```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

#### 2. AI/ML Service

```bash
gunicorn main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001 \
  --timeout 300
```

#### 3. Frontend (Nginx)

Build and serve with Nginx:

```bash
npm run build
# Copy dist/ to nginx html directory
```

Nginx config:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# AI/ML service health
curl http://localhost:8001/health

# Model runtime status
curl -H "X-API-Key: your-key" http://localhost:8001/internal/model-status
```

### Logs

- **Backend**: `logs/backend.log`
- **AI/ML**: `logs/ai_ml.log`
- **Audit**: Query `model_audit_logs` table

### Cleanup

Regular cleanup of temporary files:

```python
# Run periodically (e.g., daily cron job)
from app.modules.ai.services.model_storage_service import get_storage_service

storage = get_storage_service()
storage.cleanup_temp_files(max_age_hours=24)
```

### Backup

1. **Database**: Regular PostgreSQL backups
2. **Model Files**: Backup `models/` directory
3. **Audit Logs**: Export audit logs periodically

---

## Troubleshooting

### Issue: Model Upload Fails

**Symptoms**: 400 error during upload

**Solutions**:
1. Check file size (must be 1KB - 500MB)
2. Verify file extension (.pt, .pth, .h5, .onnx, .safetensors)
3. Check storage directory permissions
4. Review backend logs for validation errors

### Issue: Model Reload Fails

**Symptoms**: 500 error on reload

**Solutions**:
1. Verify API key is correct
2. Check model file exists at path
3. Ensure AI/ML service is running
4. Check GPU memory (if using CUDA)
5. Review AI/ML service logs

### Issue: Audit Logs Not Created

**Symptoms**: No entries in audit_logs table

**Solutions**:
1. Verify database connection
2. Check audit_service initialization
3. Ensure tables are created
4. Review backend logs for errors

### Issue: Frontend Cannot Connect

**Symptoms**: Network errors in browser console

**Solutions**:
1. Verify API_BASE_URL is correct
2. Check CORS settings in backend
3. Ensure backend is running
4. Check firewall/proxy settings

---

## Support

For additional help:
- Check API documentation: `/docs`
- Review audit logs for error details
- Contact development team

---

## Appendix: File Structure

```
skinaid-v2/
├── backend/
│   ├── app/
│   │   └── modules/ai/
│   │       ├── models/
│   │       │   ├── ai_models.py
│   │       │   └── audit_log.py
│   │       ├── repository/
│   │       │   └── model_repository.py
│   │       ├── routes/
│   │       │   └── model_management_router.py
│   │       ├── schemas/
│   │       │   └── model_schemas.py
│   │       └── services/
│   │           ├── model_service.py
│   │           ├── model_validator.py
│   │           ├── model_storage_service.py
│   │           └── audit_service.py
│   └── tests/
│       └── test_model_validator.py
├── ai_ml/
│   ├── routes/
│   │   └── model_reload.py
│   └── models/
│       ├── detection/
│       │   └── wound_detector.py
│       └── classification/
│           └── wound_classifier.py
├── frontend/
│   └── src/
│       ├── components/admin/
│       │   └── ModelManagement.tsx
│       ├── services/
│       │   └── modelManagementService.ts
│       └── types/
│           └── admin.ts
└── docs/
    └── API_MODEL_MANAGEMENT.md
```
