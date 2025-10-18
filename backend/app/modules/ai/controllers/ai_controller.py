from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, Dict, Any, List, Optional
import logging
import tempfile
import os
import aiofiles
import uuid
from datetime import datetime
from app.core.config import settings

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.ai.schemas.wound_analysis_schemas import WoundAnalysisResponse, WoundDetectionSummary
from app.modules.ai.schemas.wound_detection_schemas import WoundDetectionResponse
from app.modules.ai.models.wound_analysis import WoundAnalysis
from app.modules.ai.models.wound_detection import WoundDetection
from app.modules.ai.services.wound_ai_service import WoundAIService
from app.modules.firstaid.services.first_aid_service import FirstAidService
from app.utils.exceptions.base_exceptions import AppBaseException
from app.utils.constants.error_codes import USER_INVALID_DATA

logger = logging.getLogger(__name__)

class AIController:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = WoundAIService()
        self.first_aid_service = FirstAidService(db)
        self.upload_dir = getattr(settings, 'UPLOAD_DIR', "./uploads")
        self.base_url = getattr(settings, 'BASE_URL', "http://localhost:8000")

    def _generate_image_path(self, user_id: str, original_filename: str) -> tuple[str, str]:
        """Tạo đường dẫn lưu ảnh theo format: uploads/YYYY/MM/DD/user_id_timestamp_uuid.ext"""
        now = datetime.now()
        date_path = now.strftime("%Y/%m/%d")

        timestamp = int(now.timestamp())
        unique_id = str(uuid.uuid4())[:8]

        file_ext = os.path.splitext(original_filename)[1].lower()
        if not file_ext:
            file_ext = ".jpg"

        new_filename = f"{user_id}_{timestamp}_{unique_id}{file_ext}"
        full_path = os.path.join(getattr(settings, 'UPLOAD_DIR', "./uploads"), date_path, new_filename)

        return full_path, f"{date_path}/{new_filename}"

    def _determine_primary_and_secondary_detections(self, detections: List[Dict[str, Any]]) -> tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Chọn primary và secondary detections theo logic mới:
        1. Lọc detections có confidence >= 65%
        2. Từ các detections đạt ngưỡng, chọn primary (có severity nặng nhất, nếu bằng nhau thì chọn confidence cao hơn)
        3. Từ các detections còn lại, lọc secondary:
           - Chỉ giữ lại detections có severity cao nhất trong cùng wound_type
           - Loại bỏ các detections trùng wound_type nhưng có severity nhẹ hơn
        4. Sắp xếp secondary theo: severity > confidence
        
        Note: Xử lý severity với format "moderate_skintear" -> extract "moderate" (index [1])
        """

        if not detections:
            return None, []

        # Lọc detections đạt ngưỡng 65%
        reliable_detections = [d for d in detections if d.get("confidence", 0) >= 0.65]

        if not reliable_detections:
            logger.warning("No detections meet accuracy threshold (65%)")
            return None, []

        # Định nghĩa thứ tự ưu tiên của severity
        severity_priority = {"severe": 3, "moderate": 2, "mild": 1}
        
        # Định nghĩa thứ tự ưu tiên của burn sub-types (cho moderate)
        # Giá trị cao hơn = ưu tiên cao hơn
        burn_subtype_priority = {
            "skintear": 2,  # Ưu tiên cao nhất
            "blister": 1,   # Ưu tiên thấp hơn
        }

        def extract_base_severity(severity_str: str) -> str:
            """
            Trích xuất severity cơ bản từ severity string có thể chứa nhiều dấu "_"
            """
            severity_lower = severity_str.lower().strip()
            parts = severity_lower.split("_")
            
            # Nếu có ít nhất 2 phần, lấy phần thứ 2 (index 1)
            if len(parts) >= 2:
                base_severity = parts[1]
                # Validate base_severity
                if base_severity in severity_priority:
                    return base_severity
            
            # Nếu không có "_" hoặc phần thứ 2 không valid, kiểm tra toàn bộ string
            # hoặc tìm severity trong các parts
            for part in parts:
                if part in severity_priority:
                    return part
            
            return "mild"

        def extract_burn_subtype(severity_str: str) -> str:
            """
            Trích xuất burn sub-type từ severity string
            
            """
            severity_lower = severity_str.lower().strip()
            parts = severity_lower.split("_")
            
            # Nếu có ít nhất 3 phần (vd: burn_moderate_skintear)
            if len(parts) >= 3:
                subtype = parts[2]
                if subtype in burn_subtype_priority:
                    return subtype
            
            # Nếu có 2 phần, kiểm tra xem phần thứ 2 có phải sub-type không
            # (trường hợp: moderate_skintear)
            if len(parts) == 2:
                potential_subtype = parts[1]
                if potential_subtype in burn_subtype_priority:
                    return potential_subtype
                # Nếu không, kiểm tra index [1] là severity và tìm subtype
                # Có thể format là: "moderate_skintear" hoặc "moderate_blister"
                for i in range(len(parts)):
                    if parts[i] in burn_subtype_priority:
                        return parts[i]
            
            return ""

        def detection_priority(detection):
            severity_str = detection.get("severity", "mild")
            wound_type = detection.get("wound_type", "").lower()
            base_severity = extract_base_severity(severity_str)
            priority = severity_priority.get(base_severity, 0)
            confidence = detection.get("confidence", 0)
            
            # Trích xuất burn sub-type priority (nếu có)
            burn_subtype_score = 0
            if wound_type == "burn" and base_severity == "moderate":
                subtype = extract_burn_subtype(severity_str)
                if subtype:
                    burn_subtype_score = burn_subtype_priority.get(subtype, 0)
                    logger.debug(
                        f"Burn sub-type detected: '{subtype}' (priority: {burn_subtype_score}) "
                        f"from '{severity_str}'"
                    )
            
            # Log để debug
            if severity_str != base_severity:
                logger.debug(f"Extracted base severity '{base_severity}' from '{severity_str}'")
            
            # Return tuple: (severity_priority, burn_subtype_priority, confidence)
            # Burn subtype chỉ được xét khi wound_type=burn và severity=moderate
            return (priority, burn_subtype_score, confidence)

        # Chọn primary detection (có severity nặng nhất, nếu bằng nhau thì confidence cao hơn)
        primary_detection = max(reliable_detections, key=detection_priority)
        primary_detection["is_primary"] = True

        logger.info(f"Selected primary detection: {primary_detection.get('wound_type')} "
                    f"(confidence: {primary_detection.get('confidence')}, "
                    f"severity: {primary_detection.get('severity')})")

        # Lọc secondary detections
        remaining_detections = [d for d in reliable_detections if d != primary_detection]

        if not remaining_detections:
            return primary_detection, []

        # Nhóm theo wound_type và tìm severity cao nhất cho mỗi loại
        wound_type_groups = {}
        for detection in remaining_detections:
            wound_type = detection.get("wound_type", "unknown")
            if wound_type not in wound_type_groups:
                wound_type_groups[wound_type] = []
            wound_type_groups[wound_type].append(detection)

        # Từ mỗi nhóm wound_type, chỉ chọn detection có severity cao nhất
        # NHƯNG loại bỏ nhóm wound_type trùng với primary
        primary_wound_type = primary_detection.get("wound_type")

        secondary_detections = []
        for wound_type, type_detections in wound_type_groups.items():
            if wound_type != primary_wound_type:  # Chỉ lấy loại khác với primary
                # Chọn detection có severity cao nhất trong cùng loại
                best_in_type = max(type_detections, key=detection_priority)
                secondary_detections.append(best_in_type)

        # Sắp xếp secondary detections theo thứ tự ưu tiên
        secondary_detections.sort(key=detection_priority, reverse=True)

        logger.info(f"Selected {len(secondary_detections)} secondary detections")

        return primary_detection, secondary_detections

    def _extract_firstaid_guide_id(self, first_aid_guide: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Trích xuất firstaidguide_id từ first_aid_guide response.
        """
        if not first_aid_guide: 
            logger.debug("First aid guide is None")
            return None
        
        guide_id = first_aid_guide.get("firstaidguide_id")
        
        if guide_id:
            logger.debug(f"Extracted guide_id: {guide_id}")
        else:
            logger.warning("Guide found but no firstaidguide_id")
        
        return guide_id if guide_id else None

    def _extract_firstaid_snapshot(self, first_aid_guide: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Trích xuất firstaid snapshot từ first_aid_guide response.
        """
        if not first_aid_guide:
            logger.debug("First aid guide is None, returning default snapshot")
            return {
                "title": "Không có hướng dẫn sơ cứu",
                "description": "Không tìm thấy hướng dẫn sơ cứu phù hợp",
                "steps": [],
                "warnings": [],
                "dos": [],
                "donts": []
            }
        
        snapshot = {
            "title": first_aid_guide.get("title", ""),
            "description": first_aid_guide.get("description"),
            "steps": first_aid_guide.get("steps", []),
            "warnings": first_aid_guide.get("warnings", []),
            "dos": first_aid_guide.get("dos", []),
            "donts": first_aid_guide.get("donts", []),
            "supplies_needed": first_aid_guide.get("supplies_needed", []),
            "estimated_healing_time": first_aid_guide.get("estimated_healing_time"),
        }
        
        logger.debug(f"Extracted snapshot with title: {snapshot.get('title')}")
        return snapshot

    async def analyze_image(self, file, user_id: str) -> Union[SuccessResponse[WoundAnalysisResponse], ErrorResponse]:

        local_file_path = None
        try:
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/jpg"]
            if file.content_type not in allowed_types:
                return ErrorResponse(
                    message=f"Invalid file type: {file.content_type}. Only JPEG/PNG allowed.",
                    error_code="INVALID_FILE_TYPE",
                    error_details={"content_type": file.content_type, "allowed_types": allowed_types}
                )

            # Validate file size
            content = await file.read()
            if len(content) > 5 * 1024 * 1024:
                return ErrorResponse(
                    message="File size too large. Maximum 5MB allowed.",
                    error_code="FILE_TOO_LARGE",
                    error_details={"file_size": len(content), "max_size": 5 * 1024 * 1024}
                )

            # Generate file path và lưu image
            file_path, relative_path = self._generate_image_path(user_id, file.filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)

            image_url = f"{getattr(settings, 'BASE_URL', 'http://localhost:8000')}/uploads/{relative_path}"
            local_file_path = file_path

            # Call AI service để phân tích
            logger.info(f"Calling AI service to analyze image: {file_path}")
            ai_result = await self.ai_service.analyze_wound_image(file_path)

            if not ai_result.get("success", False):
                return ErrorResponse(
                    message=f"AI analysis failed: {ai_result.get('error', 'Unknown error')}",
                    error_code=ai_result.get("error_code", "AI_PROCESSING_ERROR"),
                    error_details={"ai_error": ai_result.get("error")}
                )

            # Xác định primary và secondary detections
            primary_detection, secondary_detections = self._determine_primary_and_secondary_detections(
                ai_result.get("detections", [])
            )

            # Case 1: Có detections nhưng không có detection nào đạt ngưỡng 65%
            if ai_result.get("num_detections", 0) > 0 and not primary_detection:
                logger.info("Detections found but none meet accuracy threshold")
                
                analysis = WoundAnalysis.create_analysis(
                    user_id=user_id,
                    image_url=image_url,
                    file_name=file.filename,
                    file_size=len(content),
                    ai_model_version=ai_result.get("ai_model_version", "YOLOv11_EfficientNetV2_1.0"),
                    total_detections=ai_result.get("num_detections", 0),
                    processing_time_ms=int(ai_result.get("processing_time", 0) * 1000),
                    primary_wound_type="not_wound",
                    primary_severity="mild",
                    primary_firstaidguide_id=None,
                    firstaid_snapshot={
                        "title": "Không phát hiện vết thương",
                        "description": "Không có hướng dẫn sơ cứu cần thiết",
                        "steps": [],
                        "warnings": [],
                        "dos": [],
                        "donts": []
                    }
                )

                self.db.add(analysis)
                await self.db.commit()
                await self.db.refresh(analysis)

                # Tạo response và override computed fields
                response_data = analysis.to_response_dict()
                response_data["average_confidence"] = 0.0
                response_data["meets_accuracy_threshold"] = False
                response_data["significant_wounds"] = []

                analysis_response = WoundAnalysisResponse(**response_data)

                return SuccessResponse(
                    message="Phân tích hình ảnh hoàn thành - không phát hiện vết thương",
                    data=analysis_response
                )

            # Case 2: Không có detections nào
            if not primary_detection:
                logger.info("No detections found")
                
                analysis = WoundAnalysis.create_analysis(
                    user_id=user_id,
                    image_url=image_url,
                    file_name=file.filename,
                    file_size=len(content),
                    ai_model_version=ai_result.get("ai_model_version", "YOLOv11_EfficientNetV2_1.0"),
                    total_detections=0,
                    processing_time_ms=int(ai_result.get("processing_time", 0) * 1000),
                    primary_wound_type="not_wound",
                    primary_severity="mild",
                    primary_firstaidguide_id=None,
                    firstaid_snapshot={
                        "title": "Không phát hiện vết thương",
                        "description": "Không có vết thương được phát hiện trong hình ảnh",
                        "steps": [],
                        "warnings": [],
                        "dos": [],
                        "donts": []
                    }
                )

                self.db.add(analysis)
                await self.db.commit()
                await self.db.refresh(analysis)

                # Tạo response và override computed fields
                response_data = analysis.to_response_dict()
                response_data["average_confidence"] = 0.0
                response_data["meets_accuracy_threshold"] = False
                response_data["significant_wounds"] = []

                analysis_response = WoundAnalysisResponse(**response_data)

                return SuccessResponse(
                    message="Phân tích hình ảnh hoàn thành - không phát hiện vết thương",
                    data=analysis_response
                )

            # Case 3: Có primary detection - lấy first aid guide
            logger.info(
                f"Getting first aid guide for {primary_detection.get('wound_type')}/{primary_detection.get('severity')}"
            )
            
            first_aid_guide = await self.first_aid_service.get_first_aid_guide(
                wound_type=primary_detection.get("wound_type", "unknown"),
                severity=primary_detection.get("severity", "mild")
            )

            if first_aid_guide:
                logger.info(
                    f"Found first aid guide: {first_aid_guide.get('firstaidguide_id')} - "
                    f"{first_aid_guide.get('title')}"
                )
            else:
                logger.warning(
                    f"First aid guide not found for "
                    f"{primary_detection.get('wound_type')}/{primary_detection.get('severity')}"
                )

            # Trích xuất guide_id và snapshot an toàn
            firstaid_guide_id = self._extract_firstaid_guide_id(first_aid_guide)
            firstaid_snapshot = self._extract_firstaid_snapshot(first_aid_guide)

            # Tạo analysis record
            analysis = WoundAnalysis.create_analysis(
                user_id=user_id,
                image_url=image_url,
                file_name=file.filename,
                file_size=len(content),
                ai_model_version=ai_result.get("ai_model_version", "YOLOv11_EfficientNetV2_1.0"),
                total_detections=ai_result.get("num_detections", 0),
                processing_time_ms=int(ai_result.get("processing_time", 0) * 1000),
                primary_wound_type="wound",
                primary_severity=primary_detection.get("severity", "mild"),
                primary_firstaidguide_id=firstaid_guide_id,  # Sẽ có giá trị nếu tìm thấy guide
                firstaid_snapshot=firstaid_snapshot  # Sẽ có đầy đủ nội dung
            )

            self.db.add(analysis)
            await self.db.commit()
            await self.db.refresh(analysis)

            # Lưu tất cả detections vào database
            all_significant_detections = [primary_detection] + secondary_detections

            for detection in all_significant_detections:
                # Với secondary detections, có thể lấy guide riêng hoặc dùng chung
                detection_guide_id = firstaid_guide_id if detection.get("is_primary") else None
                
                wound_detection = WoundDetection.create_detection(
                    analysis_id=analysis.analysis_id,
                    wound_type=detection.get("wound_type", "unknown"),
                    severity=detection.get("severity", "unknown"),
                    confidence_score=detection.get("confidence", 0.0),
                    bounding_box=detection.get("bounding_box", {}),
                    detection_index=detection.get("detection_index", 0),
                    is_primary=detection.get("is_primary", False),
                    firstaidguide_id=detection_guide_id
                )
                self.db.add(wound_detection)

            await self.db.commit()

            # Tính average confidence từ significant_detections
            avg_confidence = sum(
                d.get("confidence", 0.0) for d in all_significant_detections
            ) / len(all_significant_detections)

            # Tạo significant_wounds summary
            significant_wounds = []
            for detection in all_significant_detections:
                wound_summary = WoundDetectionSummary(
                    wound_type=detection.get("wound_type", "unknown"),
                    severity=detection.get("severity", "mild"),
                    confidence_score=detection.get("confidence", 0.0),
                    bounding_box=detection.get("bounding_box", {}),
                    is_primary=detection.get("is_primary", False)
                )
                significant_wounds.append(wound_summary)

            # Tạo response và override computed fields
            response_data = analysis.to_response_dict()
            response_data["average_confidence"] = avg_confidence
            response_data["meets_accuracy_threshold"] = avg_confidence >= 0.65
            response_data["significant_wounds"] = [wound.dict() for wound in significant_wounds]

            analysis_response = WoundAnalysisResponse(**response_data)

            logger.info(
                f"Analysis completed successfully: {analysis.analysis_id}, "
                f"guide_id: {firstaid_guide_id}, "
                f"avg_confidence: {avg_confidence:.2f}"
            )

            return SuccessResponse(
                message="Phân tích hình ảnh thành công",
                data=analysis_response
            )

        except AppBaseException as e:
            logger.error(f"AppBaseException during AI analysis: {e}")
            return ErrorResponse(
                message=e.message,
                error_code=e.error_code,
                error_details={"validation_error": str(e)}
            )

        except Exception as e:
            logger.error(f"Unexpected error during AI analysis: {e}", exc_info=True)
            return ErrorResponse(
                message="Có lỗi xảy ra trong quá trình phân tích AI",
                error_code="INTERNAL_ERROR",
                error_details={"error": str(e)}
            )

        finally:
            pass

    async def check_health(self) -> Union[SuccessResponse[dict], ErrorResponse]:
        try:
            model_health = await self.ai_service.check_model_health()

            db_healthy = True
            try:
                from sqlalchemy import text
                await self.db.execute(text("SELECT 1"))
            except Exception:
                db_healthy = False

            health_data = {
                "status": "healthy" if (model_health["overall_health"] and db_healthy) else "unhealthy",
                "ai_models": model_health,
                "database": "healthy" if db_healthy else "unhealthy",
                "accuracy_threshold": 0.65,
                "supported_wound_types": model_health["supported_wound_types"],
                "timestamp": datetime.now().isoformat()
            }

            return SuccessResponse(
                message="AI service health check completed",
                data=health_data
            )

        except Exception as e:
            logger.error(f"Error checking AI service health: {e}")
            return ErrorResponse(
                message="Không thể kiểm tra trạng thái AI service",
                error_code="HEALTH_CHECK_ERROR",
                error_details={"error": str(e)}
            )

    async def get_analysis_history(self, user_id: str) -> Union[SuccessResponse[dict], ErrorResponse]:
        try:
            from sqlalchemy import select

            query = select(WoundAnalysis).where(
                WoundAnalysis.user_id == user_id,
                WoundAnalysis.is_deleted == False
            ).order_by(WoundAnalysis.created_at.desc())

            result = await self.db.execute(query)
            analyses = result.scalars().all()

            total_analyses = len(analyses)
            successful_analyses = sum(1 for a in analyses if a.is_successful_analysis)
            avg_accuracy = sum(a.average_confidence for a in analyses) / total_analyses if total_analyses > 0 else 0

            analysis_responses = [analysis.to_response_dict() for analysis in analyses]

            return SuccessResponse(
                message="Lấy lịch sử phân tích thành công",
                data={
                    "analyses": analysis_responses,
                    "statistics": {
                        "total_analyses": total_analyses,
                        "successful_analyses": successful_analyses,
                        "success_rate": (successful_analyses / total_analyses * 100) if total_analyses > 0 else 0,
                        "average_accuracy": avg_accuracy,
                        "meets_accuracy_threshold": avg_accuracy >= 0.65
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error getting analysis history for user {user_id}: {e}")
            return ErrorResponse(
                message="Không thể lấy lịch sử phân tích",
                error_code="ANALYSIS_HISTORY_ERROR",
                error_details={"error": str(e)}
            )