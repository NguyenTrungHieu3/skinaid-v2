# AI Module - Wound Analysis and Detection
"""
AI module cung cấp phân tích và phát hiện vết thương.
- Phân tích ảnh vết thương bằng AI
- Lưu trữ kết quả và lịch sử phân tích
"""

from .models.wound_analysis import WoundAnalysis
from .models.wound_detection import WoundDetection
from .exceptions import AIError, WoundAnalysisNotFoundError, AIProcessFailedError, ImageDownloadError

__all__ = [
    "WoundAnalysis",
    "WoundDetection",
    "AIError",
    "WoundAnalysisNotFoundError",
    "AIProcessFailedError",
    "ImageDownloadError",
]
