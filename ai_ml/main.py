from fastapi import FastAPI
from middleware.cors import setup_cors
from middleware.rate_limiter import setup_rate_limiter
from routes import base, detection, classification, detection_and_classification

app = FastAPI(
    title="Wound Detection & Classification API",
    version="1.0.0",
    description="AI service for wound detection and severity classification"
)

limiter = setup_rate_limiter(app)
setup_cors(app)

app.include_router(base.router)
app.include_router(detection.router)
app.include_router(classification.router)
app.include_router(detection_and_classification.router)
