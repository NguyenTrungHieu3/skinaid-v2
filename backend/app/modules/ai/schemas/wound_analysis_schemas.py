from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
class WoundDetectionResponse(BaseModel):
    """Response schema for wound detection."""
    detection_id: UUID
    wound_type: str
    severity: str
    sub_type: Optional[str] = None
    confidence_score: float
    bounding_box: Dict[str, Any]
    detection_index: int
    firstaid_snapshot: Dict[str, Any]
class WoundAnalysisResponse(BaseModel):
    """Basic wound analysis response."""
    analysis_id: UUID
    user_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    image_url: str
    file_name: str
    total_detections: int
    processing_time_ms: int
    analyzed_at: datetime
    created_at: datetime
class WoundAnalysisDetailResponse(WoundAnalysisResponse):
    """Detailed wound analysis response with detections."""
    detections: List[WoundDetectionResponse] = Field(default_factory=list)
class WoundAnalysisListResponse(BaseModel):
    """List of wound analyses."""
    total: int
    limit: int
    offset: int
    events: List[WoundAnalysisResponse]

class BatchAnalysisItemResult(BaseModel): 
    """
    Kết quả phân tích cho MỘT ảnh trong batch.
    
    Giải thích:
    - success: True/False cho biết ảnh này được xử lý thành công không
    - file_name: Tên file gốc để client biết đây là ảnh nào
    - analysis: Kết quả phân tích (nếu thành công)
    - error: Thông tin lỗi (nếu thất bại)
    """
    success: bool = Field(
        description= "Ảnh này có được phân tích thành công không"
    )
    file_name: str = Field(
        description="Tên file gốc"
    )
    analysis: Optional[WoundAnalysisResponse] = Field(
        default=None,
        description="Kết quả phân tích nếu thành công"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Thông báo lỗi nếu thất bại"
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Mã lỗi nếu thất bại"
    )

class BatchAnalysisResponse(BaseModel):
    """
    Response tổng hợp cho batch analysis.
    
    Giải thích:
    - total_files: Tổng số file được gửi lên
    - successful: Số lượng file phân tích thành công
    - failed: Số lượng file thất bại
    - results: Danh sách kết quả chi tiết cho từng file
    - processing_time_ms: Tổng thời gian xử lý tất cả ảnh
    """
    total_files: int = Field(
        description="Tổng số file được upload"
    )
    successful: int = Field(
        description="Số lượng file phân tích thành công"
    )
    failed: int = Field(
        description="Số lượng file thất bại"
    )
    results: List[BatchAnalysisItemResult] = Field(
        description="Kết quả chi tiết cho từng file"
    )
    processing_time_ms: int = Field(
        description="Tổng thời gian xử lý (milliseconds)"
    )
    
class BatchAnalysisRequest(BaseModel):
    """
    Metadata cho batch analysis request (optional).
    
    Có thể dùng để client gửi thêm thông tin như:
    - Nhóm ảnh này thuộc về ai
    - Mô tả batch này
    - Tags, categories, v.v.
    """
    description: Optional[str] = Field(
        default=None,
        description="Mô tả cho batch này (optional)"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags để phân loại batch này (optional)"
    )