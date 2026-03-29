import asyncio
import time
from typing import List, Optional
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.exceptions import AIProcessFailedError
from app.modules.ai.mappers.response_mapper import ResponseMapper
from app.modules.ai.schemas.wound_analysis_schemas import (
    BatchAnalysisItemResult,
    BatchAnalysisResponse,
    WoundAnalysisResponse,
)
from app.modules.ai.services.wound_ai_service import WoundAIService
from app.modules.ai.services.wound_analysis_service import WoundAnalysisService
from app.shared.exceptions import BadRequestError, InternalError
from app.shared.response import SuccessResponse
from app.shared.services.file_service import FileService
from app.shared.validators.file_validator import FileValidator
from app.shared.constants import error_codes as ErrorCode
from app.shared.constants import messages as Message


class ImageProcessingService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.validator = FileValidator()
        self.file_service = FileService()
        self.ai_service = WoundAIService()
        self.analysis_service = WoundAnalysisService(db)
        self.response_mapper = ResponseMapper()

    async def process_single_image(
        self,
        file: UploadFile,
        user_id: Optional[UUID] = None,
        guest_session_id: Optional[UUID] = None,
    ) -> SuccessResponse:
        validation = await self.validator.validate_upload_file(file)
        if not validation["valid"]:
            raise BadRequestError(
                message=Message.AI_INVALID_FILE_MSG,
                details={"validation_error": validation["error"]},
            )

        subfolder = f"user/{user_id}" if user_id else f"guest/{guest_session_id}"
        save_result = await self.file_service.save_file(
            file_content=validation["content"],
            filename=file.filename,
            subfolder=subfolder,
        )

        ai_result = await self.ai_service.analyze_wound(
            image_path=save_result["file_path"]
        )

        if not ai_result.get("success", False):
            raise AIProcessFailedError(
                message="AI Analysis Failed",
                details={"ai_error": ai_result.get("error")},
            )

        processing_time_ms = ai_result.get("processing_time_ms")
        if not processing_time_ms or processing_time_ms < 1:
            processing_time_ms = max(
                1, int(ai_result.get("processing_time", 0.001) * 1000)
            )

        analysis = await self.analysis_service.create_analysis(
            user_id=user_id,
            guest_session_id=guest_session_id,
            image_url=save_result["file_url"],
            image_size_bytes=validation["size"],
        )

        if ai_result.get("detections"):
            await self.analysis_service.save_detections(
                analysis_id=analysis.analysis_id,
                detections=ai_result.get("detections", []),
            )

        analysis = await self.analysis_service.get_analysis_by_id(
            analysis.analysis_id
        )

        response_data = self.response_mapper.map_wound_analysis_basic(analysis)

        return SuccessResponse(
            message=Message.AI_ANALYSIS_SUCCESS_MSG,
            data=response_data,
        )

    async def process_batch_images(
        self,
        files: List[UploadFile],
        user_id: Optional[UUID] = None,
        guest_session_id: Optional[UUID] = None
    ) -> BatchAnalysisResponse:
        """Process multiple images."""
        start_time = time.time()

        tasks = [
            self.process_single_image(
                file=file,
                user_id=user_id,
                guest_session_id=guest_session_id
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
                error_msg = getattr(result, "message", str(result))
                batch_results.append(
                    BatchAnalysisItemResult(
                        success=False,
                        file_name=file_name,
                        error_message=error_msg,
                        error_code=ErrorCode.AI_ANALYSIS_ERROR,
                    )
                )
                failed_count += 1
                continue

            if isinstance(result, SuccessResponse):
                batch_results.append(
                    BatchAnalysisItemResult(
                        success=True,
                        file_name=file_name,
                        analysis=result.data,
                    )
                )
                successful_count += 1

        processing_time_ms = int((time.time() - start_time) * 1000)

        return BatchAnalysisResponse(
            total_files=len(files),
            successful=successful_count,
            failed=failed_count,
            results=batch_results,
            processing_time_ms=processing_time_ms
        )
