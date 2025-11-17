from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import UploadFile, HTTPException
from uuid import UUID

from app.modules.ai.models.wound_analysis import WoundAnalysis
from app.modules.ai.models.wound_detection import WoundDetection
from app.modules.guest.models.guest_session import GuestSession
from app.shared.validators.file_validator import FileValidator
from app.shared.services.file_service import FileService
from app.modules.ai.services.wound_ai_service import WoundAIService

class GuestAnalysisService:

    def __init__(self, db:AsyncSession): 
        self.db = db
        self.validator = FileValidator()
        self.file_service = FileService()
        self.ai_service = WoundAIService()


    async def upload_and_analyze(
        self, 
        session_id: UUID, 
        file: UploadFile
    )-> WoundAnalysis: 
        
        # validate session
        session = await self.db.get(GuestSession, session_id)
        if not session or not session.is_active: 
            raise HTTPException(status_code=401, detail="Session không hợp lệ")
        
        # check upload >= 3 
        if session.upload_count >= 3:
            raise HTTPException(status_code=429, detail="Đã đạt giới hạn upload (3)")
        
        # validate file
        validation = await self.validator.validate_upload_file(file)
        if not validation['valid']: 
            raise HTTPException(status_code=400, detail=validation['error'])
        
        # save file 
        save_result = await self.file_service.save_file(
            file_content=validation['content'], 
            filename=file.filename,
            subfolder=f"guest/{session_id}"
        )

        # call ai service
        ai_result = await self.ai_service.analyze_wound_image(
            image_path=save_result['file_path']
        )

        analysis = WoundAnalysis.create_analysis(
            user_id=None, 
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
            wound_detection = WoundDetection(
                analysis_id=analysis.analysis_id,
                wound_type=detection['wound_type'],
                severity=detection['severity'],
                sub_type=detection.get('sub_type'),
                confidence_score=detection['confidence'],
                bounding_box=detection['bounding_box'],
                detection_index=idx,
                firstaidguide_id=detection.get('firstaidguide_id'),
                firstaid_snapshot=detection.get('firstaid_snapshot')
            )
            self.db.add(wound_detection)
        
        # Update session counters
        session.upload_count += 1
        session.analysis_count += 1
        
        await self.db.commit()
        await self.db.refresh(analysis)
        
        return analysis
    
    async def get_guest_history(
        self,
        session_id: UUID
    ) -> list[WoundAnalysis]:
        """Get all analyses for a guest session"""
        from sqlmodel import select
        
        statement = select(WoundAnalysis).where(
            WoundAnalysis.session_id == session_id,
            WoundAnalysis.is_deleted == False
        ).order_by(WoundAnalysis.created_at.desc())
        
        result = await self.db.execute(statement)
        return result.scalars().all()