from fastapi import HTTPException, status
import asyncio
from fastapi import UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from typing import Optional, Union, List

from app.shared.validators.file_validator import FileValidator
from app.shared.services.file_service import FileService
from app.shared.mappers.response_mapper import ResponseMapper
from app.shared.schemas.response import SuccessResponse, ErrorResponse

from app.modules.ai.models.wound_analysis import WoundAnalysis
from app.modules.ai.models.wound_detection import WoundDetection
from app.modules.ai.services.wound_ai_service import WoundAIService
from app.modules.ai.services.wound_analysis_service import WoundAnalysisService
from app.modules.ai.schemas.wound_analysis_schemas import (
    WoundAnalysisResponse,
    BatchAnalysisResponse,
    BatchAnalysisItemResult
)
from app.modules.firstaid.services.first_aid_service import FirstAidService

from app.utils.constants import error_codes as ErrorCode
from app.utils.constants import messages as Message

import logging
logger = logging.getLogger(__name__)


class ImageProcessingService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.validator = FileValidator()
        self.file_service = FileService()
        self.ai_service = WoundAIService()
        self.analysis_service = WoundAnalysisService(db)
        self.first_aid_service = FirstAidService(db)
        self.response_mapper = ResponseMapper()
    
    async def process_single_image(
        self,
        file: UploadFile,
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
    ) -> Union[SuccessResponse[WoundAnalysisResponse], ErrorResponse]:
       
        try:
            logger.debug(f"[PROCESS_SINGLE] Processing file: {file.filename}")
            
            validation = await self.validator.validate_upload_file(file)
            if not validation['valid']:
                logger.warning(
                    f"[PROCESS_SINGLE] File '{file.filename}' validation failed: "
                    f"{validation['error']}"
                )
                return ErrorResponse(
                    message=Message.AI_INVALID_FILE_MSG,
                    error_code=ErrorCode.AI_INVALID_FILE,
                    error_details={"validation_error": validation['error']},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Tạo subfolder theo user_id hoặc session_id để sắp xếp files
            subfolder = f"user/{user_id}" if user_id else f"guest/{session_id}"
            
            save_result = await self.file_service.save_file(
                file_content=validation['content'],
                filename=file.filename,
                subfolder=subfolder
            )
            
            logger.debug(
                f"[PROCESS_SINGLE] File saved: {save_result['file_url']}"
            )
            
            ai_result = await self.ai_service.analyze_wound(
                image_path=save_result['file_path']
            )
            
            # Kiểm tra AI có trả về lỗi không
            if not ai_result.get('success', False):
                logger.error(
                    f"[PROCESS_SINGLE] AI analysis failed for '{file.filename}': "
                    f"{ai_result.get('error', 'Unknown error')}"
                )
                return ErrorResponse(
                    message="Phân tích AI thất bại",
                    error_code=ai_result.get('error_code', ErrorCode.AI_ANALYSIS_ERROR),
                    error_details={"ai_error": ai_result.get('error')},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            analysis = WoundAnalysis.create_analysis(
                user_id=user_id,
                session_id=session_id,
                image_url=save_result['file_url'],
                file_name=save_result['filename'],
                file_size=validation['size'],
                total_detections=len(ai_result.get('detections', [])),
                processing_time_ms=ai_result.get('processing_time_ms', 0)
            )
            
            self.db.add(analysis)
            await self.db.flush() 
            
            for idx, detection in enumerate(ai_result.get('detections', [])):
                # Lấy hướng dẫn sơ cứu cho detection này
                guide = await self.first_aid_service.get_first_aid_guide(
                    wound_type=detection['wound_type'],
                    severity=detection['severity'],
                    sub_type=detection.get('sub_type')
                )
                
                # Trích xuất guide ID và snapshot để lưu vào detection
                guide_id = guide.get('firstaidguide_id') if guide else None
                snapshot = self.analysis_service.extract_snapshot(guide)
                
                # Tạo WoundDetection record
                wound_detection = WoundDetection(
                    analysis_id=analysis.analysis_id,
                    wound_type=detection['wound_type'],
                    severity=detection['severity'],
                    sub_type=detection.get('sub_type'),
                    confidence_score=detection['confidence'],
                    bounding_box=detection.get('bounding_box'),
                    detection_index=idx,
                    firstaidguide_id=guide_id,
                    firstaid_snapshot=snapshot
                )
                self.db.add(wound_detection)
            
            await self.db.commit()
            await self.db.refresh(analysis, ['wound_detections'])
            
            response_data = self.response_mapper.map_wound_analysis_basic(analysis)
            
            logger.debug(
                f"[PROCESS_SINGLE] Success for '{file.filename}': "
                f"{analysis.analysis_id}"
            )
            
            return SuccessResponse(
                message=Message.AI_ANALYSIS_SUCCESS_MSG,
                data=response_data,
                status_code=status.HTTP_201_CREATED
            )
            
        except HTTPException as e:
            logger.error(
                f"[PROCESS_SINGLE] HTTPException for '{file.filename}': {e.detail}"
            )
            return ErrorResponse(
                message=e.message,
                error_code=e.error_code or ErrorCode.AI_ANALYSIS_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                f"[PROCESS_SINGLE] Unexpected error for '{file.filename}'",
                exc_info=True
            )
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    async def process_batch_images(
        self,
        files: List[UploadFile],
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
    ) -> BatchAnalysisResponse:
        """
        Xử lý phân tích cho NHIỀU ảnh vết thương cùng lúc (batch processing).
        
        Flow:
        1. Tạo tasks cho tất cả files
        2. Execute parallel với asyncio.gather()
        3. Process từng result (Exception/ErrorResponse/SuccessResponse)
        4. Calculate statistics (success/failed/time)
        5. Build và return BatchAnalysisResponse
        """
        import time
        start_time = time.time()
        
        logger.info(
            f"[BATCH_PROCESS] Starting batch analysis - "
            f"files: {len(files)}, user: {user_id}, session: {session_id}"
        )
        
        tasks = [
            self.process_single_image(
                file=file,
                user_id=user_id,
                session_id=session_id
            )
            for file in files
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        batch_results = []
        successful_count = 0
        failed_count = 0
        
        for idx, result in enumerate(results):
            file_name = files[idx].filename
            
            if isinstance(result, Exception):
                logger.error(
                    f"[BATCH_PROCESS] File '{file_name}' failed with exception: {result}"
                )
                batch_results.append(BatchAnalysisItemResult(
                    success=False,
                    file_name=file_name,
                    error_message=str(result),
                    error_code=ErrorCode.AI_ANALYSIS_ERROR
                ))
                failed_count += 1
                continue
            
            if isinstance(result, ErrorResponse):
                logger.warning(
                    f"[BATCH_PROCESS] File '{file_name}' failed: {result.message}"
                )
                batch_results.append(BatchAnalysisItemResult(
                    success=False,
                    file_name=file_name,
                    error_message=result.message,
                    error_code=result.error_code
                ))
                failed_count += 1
                continue

            if isinstance(result, SuccessResponse):
                logger.info(
                    f"[BATCH_PROCESS] File '{file_name}' analyzed successfully"
                )
                batch_results.append(BatchAnalysisItemResult(
                    success=True,
                    file_name=file_name,
                    analysis=result.data
                ))
                successful_count += 1
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"[BATCH_PROCESS] Completed - "
            f"Total: {len(files)}, Success: {successful_count}, "
            f"Failed: {failed_count}, Time: {processing_time_ms}ms"
        )
        
        return BatchAnalysisResponse(
            total_files=len(files),
            successful=successful_count,
            failed=failed_count,
            results=batch_results,
            processing_time_ms=processing_time_ms
        )

