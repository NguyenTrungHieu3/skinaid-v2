from fastapi import UploadFile, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from typing import Optional

from app.shared.validators.file_validator import FileValidator
from app.shared.services.file_service import FileService
from app.shared.mappers.response_mapper import ResponseMapper
from app.modules.ai.models.wound_analysis import WoundAnalysis
from app.modules.ai.models.wound_detection import WoundDetection
from app.modules.ai.services.wound_ai_service import WoundAIService
from app.modules.ai.services.wound_analysis_service import WoundAnalysisService
from app.modules.firstaid.services.first_aid_service import FirstAidService

class AIController:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.validator = FileValidator()
        self.file_service = FileService()
        self.ai_service = WoundAIService()
        self.analysis_service = WoundAnalysisService(db)
        self.first_aid_service = FirstAidService(db)
        self.response_mapper = ResponseMapper()

    async def analyze_image(
        self,
        file: UploadFile,
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
    ) -> dict:

        if user_id is None and session_id is None:
            raise HTTPException(
                status_code=400,
                detail="Phải cung cấp user_id hoặc session_id"
            )

        if user_id is not None and session_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Không thể cung cấp cả user_id và session_id"
            )

        # validate file
        validation = await self.validator.validate_upload_file(file)

        if not validation['valid']:
            raise HTTPException(status_code=400, detail=validation['error'])

        subfolder = f"user/{user_id}" if user_id else f"guest/{session_id}"
        save_result = await self.file_service.save_file(
            file_content=validation['content'],
            filename=file.filename,
            subfolder=subfolder
        )

        ai_result = await self.ai_service.analyze_wound(
            image_path=save_result['file_path']
        )

        # Create WoundAnalysis record
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

        # Create WoundDetection records
        for idx, detection in enumerate(ai_result.get('detections', [])):
            # Get first aid guide for this detection
            guide = await self.first_aid_service.get_first_aid_guide(
                wound_type=detection['wound_type'],
                severity=detection['severity'],
                sub_type=detection.get('sub_type')
            )

            # Extract guide ID and snapshot
            guide_id = guide.get('firstaidguide_id') if guide else None
            snapshot = self.analysis_service.extract_snapshot(guide)

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
        # Eager load wound_detections relationship để tránh MissingGreenlet error khi mapper truy cập
        await self.db.refresh(analysis, ['wound_detections'])

        #Format response (basic - minimal information)
        return self.response_mapper.map_wound_analysis_basic(analysis)
        #Format response (basic - without detailed firstaid info)
        return self.response_mapper.map_wound_analysis(
            analysis,
            include_detections=True,
            include_firstaid_details=False
        )

    async def get_analysis_history(
        self,
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        analyses = await self.analysis_service.get_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            offset=offset
        )

        return {
            'total': len(analyses),
            'limit': limit,
            'offset': offset,
            'analyses': [
                self.response_mapper.map_wound_analysis(a, include_detections=False)
                for a in analyses
            ]
        }

    async def get_analysis_detail(
        self,
        analysis_id: UUID,
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
    ) -> dict:
        analysis = await self.analysis_service.get_by_id(analysis_id)

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        if user_id is not None:
            request_user_id = UUID(user_id) if isinstance(user_id, str) else user_id
            if analysis.user_id and analysis.user_id != request_user_id:
                raise HTTPException(status_code=403, detail="Access denied")

        if session_id is not None:
            request_session_id = UUID(session_id) if isinstance(session_id, str) else session_id
            if analysis.session_id and analysis.session_id != request_session_id:
                raise HTTPException(status_code=403, detail="Access denied")

        return self.response_mapper.map_wound_analysis(
            analysis,
            include_detections=True
        )