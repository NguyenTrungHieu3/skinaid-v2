# from fastapi import FastAPI, UploadFile, File, Header, HTTPException
# from fastapi.responses import JSONResponse
# import numpy as np
# import cv2
# import sys
# import time
# from pathlib import Path
# from typing import Dict, Any
# import os
# from dotenv import load_dotenv

# app = FastAPI(
#     title="Wound Detection & Classification API",
#     version="1.0.0",
#     description="AI service for wound detection and severity classification"
# )

# load_dotenv()
# AI_API_KEY = os.getenv("AI_API_KEY")

# ai_ml_root = Path(__file__).parent.parent
# sys.path.insert(0, str(ai_ml_root))

# from middleware.cors import setup_cors
# from pipeline.analyzer import WoundAnalyzer
# analyzer = WoundAnalyzer(
#     yolo_model_path=str(ai_ml_root/"models/detection/weights/model_2_class_v1.pt"),
#     efficientnet_model_path=str(ai_ml_root/"models/classification/weights/final_model.pth")
# )

# # Setup CORS middleware
# setup_cors(app)

# @app.get("/")
# async def root():
#     """Root endpoint"""
#     return {
#         "service": "Wound Detection & Classification API",
#         "version": "1.0.0",
#         "status": "running"
#     }

# @app.get("/health")
# async def health_check():
#     """Health check endpoint - Backend gọi endpoint này để kiểm tra AI service"""
#     return {
#         "status": "healthy",
#         "service": "AI",
#         "timestamp": time.time()
#     }

# @app.post("/detect_and_classify")
# async def detect(file: UploadFile = File(...), x_api_key: str = Header(None, alias="X-API-Key")) -> Dict[str, Any]:
#     if not x_api_key or x_api_key != AI_API_KEY:
#         raise HTTPException(status_code=403, detail="Invalid API key")
    
#     try:
#         start_time = time.time()
        
#         # Read file
#         contents = await file.read()
#         np_array = np.frombuffer(contents, np.uint8)
#         img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

#         if img is None:
#             return {
#                 "success": False,
#                 "error": "Can not read image",
#                 "error_code": "INVALID_IMAGE",
#                 "num_detections": 0,
#                 "detections": []
#             }
        
#         # Gọi pipeline detect và classify
#         results = analyzer.analyze(img)
        
#         processing_time = time.time() - start_time
        
#         # Format response theo format backend expect
#         response = {
#             "success": True,
#             "num_detections": len(results) if results else 0,
#             "detections": results if results else [],
#             "processing_time": round(processing_time, 3),
#             "ai_model_version": "yolo_v11 + efficientnet_b0"
#         }
        
#         return response
        
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e),
#             "error_code": "PROCESSING_ERROR",
#             "num_detections": 0,
#             "detections": []
#         }

# @app.get("/model-info")
# async def get_model_info():
#     return {
#         "detection_model": "YOLO v11",
#         "classification_model": "EfficientNet B0",
#         "detection_model_path": "detection/models/model_2_class_v1.pt",
#         "classification_model_path": "classification/models/final_model.pth",
#         "num_wound_classes": 7,
#         "wound_classes": [
#             "abrasion mild",
#             "abrasion moderate", 
#             "bruise mild",
#             "bruise moderate",
#             "burn mild",
#             "burn moderate blister",
#             "burn moderate skintear"
#         ]
#     }