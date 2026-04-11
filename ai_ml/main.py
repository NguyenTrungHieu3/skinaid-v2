from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from middleware.cors import setup_cors
from middleware.rate_limiter import setup_rate_limiter
from routes import base, detection, classification, detection_and_classification
from configs.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup: validate model files before accepting requests ──
    detection_path = Path(settings.YOLO_MODEL_PATH)
    classification_path = Path(settings.EFFICIENTNET_MODEL_PATH)

    errors = []
    if not detection_path.exists():
        errors.append(f"Detection model NOT FOUND: {detection_path}")
    elif detection_path.stat().st_size == 0:
        errors.append(f"Detection model is EMPTY (0 bytes): {detection_path}")

    if not classification_path.exists():
        errors.append(f"Classification model NOT FOUND: {classification_path}")
    elif classification_path.stat().st_size == 0:
        errors.append(f"Classification model is EMPTY (0 bytes): {classification_path}")

    if errors:
        raise RuntimeError("AI Service startup failed — model validation errors:\n" + "\n".join(errors))

    det_mb = detection_path.stat().st_size / 1_000_000
    cls_mb = classification_path.stat().st_size / 1_000_000
    print("=" * 50)
    print("AI Service starting...")
    print(f"  Detection model   : {detection_path} ({det_mb:.1f} MB) ✓")
    print(f"  Classification model: {classification_path} ({cls_mb:.1f} MB) ✓")
    print("=" * 50)

    yield

    # ── Shutdown ──
    print("AI Service stopped.")


app = FastAPI(
    title="Wound Detection & Classification API",
    version="1.0.0",
    description="AI service for wound detection and severity classification",
    lifespan=lifespan,
)

limiter = setup_rate_limiter(app)
setup_cors(app)

app.include_router(base.router)
app.include_router(detection.router)
app.include_router(classification.router)
app.include_router(detection_and_classification.router)
