from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text
import logging
import uuid
import json

from app.modules.firstaid.models.firstaid_guide import FirstAidGuide

logger = logging.getLogger(__name__)


class FirstAidService:
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_first_aid_guide(
        self,
        wound_type: str,
        severity: str,
        sub_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        try:
            logger.info(
                f"[FIRSTAID_SERVICE] Đang lấy hướng dẫn sơ cứu: wound_type={wound_type}, "
                f"severity={severity}, sub_type={sub_type}"
            )

            if sub_type:
                specific_guide = await self._find_guide_specific(
                    wound_type, severity, sub_type
                )
                if specific_guide:
                    logger.info(f"[FIRSTAID_SERVICE] Tìm thấy hướng dẫn cụ thể với sub_type={sub_type}")
                    return self._format_guide_response(specific_guide)

                logger.warning(
                    f"[FIRSTAID_SERVICE] Không tìm thấy hướng dẫn với sub_type={sub_type}, thử hướng dẫn chung"
                )

            general_guide = await self._find_guide_general(wound_type, severity)

            if general_guide:
                logger.info("[FIRSTAID_SERVICE] Tìm thấy hướng dẫn chung")
                return self._format_guide_response(general_guide)

            logger.warning(f"[FIRSTAID_SERVICE] Không tìm thấy hướng dẫn cho {wound_type}/{severity}")
            return None

        except Exception as e:
            logger.error(f"[FIRSTAID_SERVICE] Lỗi khi lấy hướng dẫn sơ cứu: {e}", exc_info=True)
            return None

    async def _find_guide_specific(
        self,
        wound_type: str,
        severity: str,
        sub_type: str
    ) -> Optional[Dict[str, Any]]:
        try:
            sql = text("""
                SELECT *
                FROM firstaid_guides
                WHERE LOWER(wound_type) = LOWER(:wound_type)
                  AND LOWER(severity) = LOWER(:severity)
                  AND LOWER(sub_type) = LOWER(:sub_type)
                  AND is_active = true
                  AND is_deleted = false
                ORDER BY version DESC
                LIMIT 1
            """)

            result = await self.db.execute(sql, {
                "wound_type": wound_type,
                "severity": severity,
                "sub_type": sub_type
            })

            row = result.mappings().first()
            return dict(row) if row else None

        except Exception as e:
            logger.error(f"[FIRSTAID_SERVICE] Lỗi khi tìm hướng dẫn cụ thể: {e}")
            return None

    async def _find_guide_general(
        self,
        wound_type: str,
        severity: str
    ) -> Optional[Dict[str, Any]]:
        try:
            sql = text("""
                SELECT *
                FROM firstaid_guides
                WHERE LOWER(wound_type) = LOWER(:wound_type)
                  AND LOWER(severity) = LOWER(:severity)
                  AND is_active = true
                  AND is_deleted = false
                  AND (sub_type IS NULL OR sub_type = '')
                ORDER BY version DESC
                LIMIT 1
            """)

            result = await self.db.execute(sql, {
                "wound_type": wound_type,
                "severity": severity
            })

            row = result.mappings().first()
            return dict(row) if row else None

        except Exception as e:
            logger.error(f"[FIRSTAID_SERVICE] Lỗi khi tìm hướng dẫn chung: {e}")
            return None

    def _format_guide_response(self, guide: Dict[str, Any]) -> Dict[str, Any]:
        firstaidguide_id_str = guide.get("firstaidguide_id")
        created_by_str = guide.get("created_by")

        return {
            "firstaidguide_id": str(firstaidguide_id_str) if firstaidguide_id_str else None,
            "wound_type": guide.get("wound_type"),
            "severity": guide.get("severity"),
            "sub_type": guide.get("sub_type"),
            "title": guide.get("title"),
            "steps": FirstAidGuide.extract_list(guide.get("steps")),
            "dos": FirstAidGuide.extract_list(guide.get("dos")),
            "donts": FirstAidGuide.extract_list(guide.get("donts")),
            "supplies_needed": FirstAidGuide.extract_list(guide.get("supplies_needed")),
            "estimated_healing_time": guide.get("estimated_healing_time"),
            "source": guide.get("source"),
            "is_active": guide.get("is_active"),
            "version": guide.get("version"),
            "created_by": str(created_by_str) if created_by_str else None,
            "created_at": guide.get("created_at"),
            "updated_at": guide.get("updated_at"),
            "is_deleted": guide.get("is_deleted", False)
        }

    async def get_available_wound_types(self) -> List[Dict[str, Any]]:
        try:
            sql = text("""
                SELECT DISTINCT wound_type, severity
                FROM firstaid_guides
                WHERE is_active = true
                  AND is_deleted = false
                ORDER BY wound_type, severity
            """)

            result = await self.db.execute(sql)
            rows = result.mappings().all()

            wound_types = {}
            for row in rows:
                wound_type = row["wound_type"]
                severity = row["severity"]

                if wound_type not in wound_types:
                    wound_types[wound_type] = {
                        "wound_type": wound_type,
                        "severities": []
                    }

                if severity not in wound_types[wound_type]["severities"]:
                    wound_types[wound_type]["severities"].append(severity)

            return list(wound_types.values())

        except Exception as e:
            logger.error(f"[FIRSTAID_SERVICE] Không thể lấy các loại vết thương có sẵn: {e}")
            return []

    async def search_first_aid_guides(
        self,
        wound_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            where_conditions = []
            params = {"limit": limit, "offset": offset}

            if is_active is not None:
                where_conditions.append("is_active = :is_active")
                params["is_active"] = is_active

            if wound_type:
                where_conditions.append("LOWER(wound_type) = LOWER(:wound_type)")
                params["wound_type"] = wound_type

            if severity:
                where_conditions.append("LOWER(severity) = LOWER(:severity)")
                params["severity"] = severity

            if search:
                where_conditions.append("title ILIKE :search")
                params["search"] = f"%{search}%"

            where_conditions.append("is_deleted = false")

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Get total count
            count_sql = text(f"""
                SELECT COUNT(*) FROM firstaid_guides
                WHERE {where_clause}
            """)
            count_result = await self.db.execute(count_sql, params)
            total_count = count_result.scalar()

            # Get paginated items
            sql = text(f"""
                SELECT * FROM firstaid_guides
                WHERE {where_clause}
                ORDER BY wound_type, severity
                LIMIT :limit OFFSET :offset
            """)

            result = await self.db.execute(sql, params)
            rows = result.mappings().all()

            guides = []
            for row in rows:
                guide = dict(row)
                guides.append(self._format_guide_response(guide))

            logger.info(f"Tìm thấy {len(guides)} hướng dẫn sơ cứu (Tổng: {total_count})")
            return {
                "items": guides,
                "total": total_count
            }

        except Exception as e:
            logger.error(f"[FIRSTAID_SERVICE] Không thể tìm kiếm hướng dẫn sơ cứu: {e}")
            return {
                "items": [],
                "total": 0
            }

    async def get_guide_statistics(self) -> Dict[str, Any]:
        try:
            # Total guides (both active and inactive)
            total_query = text("""
                SELECT COUNT(*) as total 
                FROM firstaid_guides 
                WHERE is_deleted = false
            """)
            total_result = await self.db.execute(total_query)
            total_guides = total_result.scalar()

            # Active guides
            active_query = text("""
                SELECT COUNT(*) as total 
                FROM firstaid_guides 
                WHERE is_active = true
                  AND is_deleted = false
            """)
            active_result = await self.db.execute(active_query)
            active_guides = active_result.scalar()

            type_query = text("""
                SELECT wound_type, COUNT(*) as count
                FROM firstaid_guides
                WHERE is_active = true
                  AND is_deleted = false
                GROUP BY wound_type
                ORDER BY count DESC
            """)
            type_result = await self.db.execute(type_query)
            type_stats = type_result.mappings().all()

            severity_query = text("""
                SELECT severity, COUNT(*) as count
                FROM firstaid_guides
                WHERE is_active = true
                  AND is_deleted = false
                GROUP BY severity
                ORDER BY count DESC
            """)
            severity_result = await self.db.execute(severity_query)
            severity_stats = severity_result.mappings().all()

            return {
                "total_guides": total_guides,
                "active_guides": active_guides,
                "wound_type_breakdown": {
                    row["wound_type"]: row["count"] for row in type_stats
                },
                "severity_breakdown": {
                    row["severity"]: row["count"] for row in severity_stats
                },
                "coverage_percentage": min(100, (active_guides / 15) * 100)
            }

        except Exception as e:
            logger.error(f"[FIRSTAID_SERVICE] Không thể lấy thống kê hướng dẫn: {e}")
            return {
                "total_guides": 0,
                "wound_type_breakdown": {},
                "severity_breakdown": {},
                "coverage_percentage": 0
            }

    async def validate_guide_completeness(
        self, 
        guide_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        issues = []

        required_fields = ["wound_type", "severity", "title"]
        for field in required_fields:
            if not guide_data.get(field):
                issues.append(f"Thiếu trường bắt buộc: {field}")

        if not guide_data.get("steps"):
            issues.append("Thiếu thông tin các bước thực hiện")

        if not guide_data.get("dos"):
            issues.append("Thiếu 'dos' (những việc nên làm)")

        if not guide_data.get("donts"):
            issues.append("Thiếu 'donts' (những việc không nên làm)")

        return {
            "is_complete": len(issues) == 0,
            "issues": issues,
            "completeness_score": max(0, 100 - len(issues) * 20)
        }

    async def create_first_aid_guide(
        self,
        guide_data: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """Tạo hướng dẫn sơ cứu mới."""
        try:
            # Check for existing active guide with same wound_type, severity, and sub_type
            wound_type = guide_data["wound_type"]
            severity = guide_data["severity"]
            sub_type = guide_data.get("sub_type")
            is_active = guide_data.get("is_active", True)

            if is_active:
                # Check for active guides that are NOT deleted
                existing_active = await self._find_guide_specific(wound_type, severity, sub_type) if sub_type else await self._find_guide_general(wound_type, severity)
                
                if existing_active:
                    msg = f"Hướng dẫn hoạt động đã tồn tại cho {wound_type} - {severity}"
                    if sub_type:
                        msg += f" ({sub_type})"
                    raise ValueError(msg)

            # Convert lists to JSONB format
            steps_jsonb = {"items": guide_data.get("steps", [])}
            dos_jsonb = {"items": guide_data.get("dos", [])} if guide_data.get("dos") else None
            donts_jsonb = {"items": guide_data.get("donts", [])} if guide_data.get("donts") else None
            supplies_jsonb = {"items": guide_data.get("supplies_needed", [])} if guide_data.get("supplies_needed") else None
            
            # Convert source string to JSONB format
            source_value = guide_data.get("source")
            source_jsonb = {"source": source_value} if source_value else None

            guide = FirstAidGuide.create_guide(
                wound_type=guide_data["wound_type"],
                severity=guide_data["severity"],
                title=guide_data["title"],
                sub_type=guide_data.get("sub_type"),
                steps=steps_jsonb,
                dos=dos_jsonb,
                donts=donts_jsonb,
                supplies_needed=supplies_jsonb,
                source=source_jsonb,
                estimated_healing_time=guide_data.get("estimated_healing_time"),
                created_by=str(created_by) if created_by else None
            )

            # Ensure is_active is set correctly from input
            guide.is_active = is_active

            self.db.add(guide)
            await self.db.commit()
            await self.db.refresh(guide)

            logger.info(f"Đã tạo hướng dẫn sơ cứu: {guide.firstaidguide_id}")
            
            # Chuyển đổi sang dict cho response
            return self._model_to_dict(guide)

        except ValueError as e:
            # Re-raise ValueError to be handled by controller
            raise e
        except Exception as e:
            await self.db.rollback()
            error_str = str(e).lower()
            if "chk_sub_type_valid" in error_str:
                raise ValueError(f"Invalid sub_type '{guide_data.get('sub_type')}' for wound_type '{guide_data.get('wound_type')}'. Please check allowed sub-types.")
            
            logger.error(f"Failed to create first aid guide: {e}", exc_info=True)
            raise

    async def update_first_aid_guide(
        self,
        guide_id: uuid.UUID,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Cập nhật hướng dẫn sơ cứu."""
        try:
            # Tìm hướng dẫn hiện tại
            sql = text("""
                SELECT * FROM firstaid_guides
                WHERE firstaidguide_id = :guide_id
            """)
            
            result = await self.db.execute(sql, {"guide_id": guide_id})
            existing_guide = result.mappings().first()
            
            if not existing_guide:
                logger.warning(f"Không tìm thấy hướng dẫn: {guide_id}")
                return None

            # Check for duplicate active guide if setting to active
            if update_data.get("is_active") is True:
                wound_type = existing_guide.wound_type
                severity = existing_guide.severity
                sub_type = existing_guide.sub_type
                
                # Check against other guides
                check_sql = text("""
                    SELECT 1 FROM firstaid_guides
                    WHERE LOWER(wound_type) = LOWER(:wound_type)
                      AND LOWER(severity) = LOWER(:severity)
                      AND (LOWER(sub_type) = LOWER(:sub_type) OR (:sub_type IS NULL AND sub_type IS NULL))
                      AND is_active = true
                      AND is_deleted = false
                      AND firstaidguide_id != :guide_id
                """)
                
                check_result = await self.db.execute(check_sql, {
                    "wound_type": wound_type,
                    "severity": severity,
                    "sub_type": sub_type,
                    "guide_id": guide_id
                })
                
                if check_result.first():
                    msg = f"Hướng dẫn hoạt động đã tồn tại cho {wound_type} - {severity}"
                    if sub_type:
                        msg += f" ({sub_type})"
                    raise ValueError(msg)

            # Whitelist of allowed fields to prevent SQL injection
            allowed_fields = {
                "title", "steps", "dos", 
                "donts", "supplies_needed", "source", "estimated_healing_time", "is_active"
            }
            
            # Prepare update fields
            update_fields = []
            params = {"guide_id": guide_id}
            
            if "title" in update_data and "title" in allowed_fields:
                update_fields.append("title = :title")
                params["title"] = update_data["title"]
            
            if "steps" in update_data and "steps" in allowed_fields:
                update_fields.append("steps = :steps")
                # Fix JSONB encoding: use json.dumps() to serialize dict to JSON string
                params["steps"] = json.dumps({"items": update_data["steps"]})
            
            if "dos" in update_data and "dos" in allowed_fields:
                update_fields.append("dos = :dos")
                # Fix JSONB encoding: use json.dumps() to serialize dict to JSON string
                params["dos"] = json.dumps({"items": update_data["dos"]}) if update_data["dos"] else None
            
            if "donts" in update_data and "donts" in allowed_fields:
                update_fields.append("donts = :donts")
                # Fix JSONB encoding: use json.dumps() to serialize dict to JSON string
                params["donts"] = json.dumps({"items": update_data["donts"]}) if update_data["donts"] else None
            
            if "supplies_needed" in update_data and "supplies_needed" in allowed_fields:
                update_fields.append("supplies_needed = :supplies_needed")
                # Fix JSONB encoding: use json.dumps() to serialize dict to JSON string
                params["supplies_needed"] = json.dumps({"items": update_data["supplies_needed"]}) if update_data["supplies_needed"] else None
            
            if "source" in update_data and "source" in allowed_fields:
                update_fields.append("source = :source")
                # Convert dict to JSON string for JSONB column
                params["source"] = json.dumps(update_data["source"]) if update_data["source"] else None
            
            if "estimated_healing_time" in update_data and "estimated_healing_time" in allowed_fields:
                update_fields.append("estimated_healing_time = :estimated_healing_time")
                params["estimated_healing_time"] = update_data["estimated_healing_time"]
            
            
            if "is_active" in update_data and "is_active" in allowed_fields:
                update_fields.append("is_active = :is_active")
                params["is_active"] = update_data["is_active"]
            
            if not update_fields:
                logger.warning("Không có trường nào để cập nhật")
                return dict(existing_guide)
            
            # Thêm updated_at
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_fields.append("version = version + 1")
            
            # Thực thi cập nhật
            update_sql = text(f"""
                UPDATE firstaid_guides
                SET {", ".join(update_fields)}
                WHERE firstaidguide_id = :guide_id
                RETURNING *
            """)
            
            result = await self.db.execute(update_sql, params)
            updated_guide = result.mappings().first()
            await self.db.commit()
            
            logger.info(f"Đã cập nhật hướng dẫn sơ cứu: {guide_id}")
            return self._format_guide_response(dict(updated_guide))

        except ValueError as e:
            raise e
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[FIRSTAID_SERVICE] Không thể cập nhật hướng dẫn sơ cứu: {e}", exc_info=True)
            raise

    async def delete_first_aid_guide(
        self,
        guide_id: uuid.UUID,
        hard_delete: bool = False
    ) -> bool:
        """Xóa hướng dẫn sơ cứu (soft delete hoặc hard delete)."""
        try:
            if hard_delete:
                # Hard delete - xóa vĩnh viễn
                sql = text("""
                    DELETE FROM firstaid_guides
                    WHERE firstaidguide_id = :guide_id
                    RETURNING firstaidguide_id
                """)
            else:
                # Soft delete - set is_deleted = true and is_active = false
                sql = text("""
                    UPDATE firstaid_guides
                    SET is_active = false, is_deleted = true, updated_at = CURRENT_TIMESTAMP
                    WHERE firstaidguide_id = :guide_id
                    RETURNING firstaidguide_id
                """)
            
            result = await self.db.execute(sql, {"guide_id": guide_id})
            deleted = result.mappings().first()
            
            if not deleted:
                logger.warning(f"Không tìm thấy hướng dẫn để xóa: {guide_id}")
                return False
            
            await self.db.commit()
            
            delete_type = "cứng" if hard_delete else "mềm"
            logger.info(f"Đã xóa {delete_type} hướng dẫn sơ cứu: {guide_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"[FIRSTAID_SERVICE] Không thể xóa hướng dẫn sơ cứu: {e}", exc_info=True)
            raise

    async def get_guide_by_id(self, guide_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Lấy hướng dẫn sơ cứu theo ID."""
        try:
            sql = text("""
                SELECT * FROM firstaid_guides
                WHERE firstaidguide_id = :guide_id
            """)
            
            result = await self.db.execute(sql, {"guide_id": guide_id})
            guide = result.mappings().first()
            
            if not guide:
                return None
            
            return self._format_guide_response(dict(guide))

        except Exception as e:
            logger.error(f"[FIRSTAID_SERVICE] Không thể lấy hướng dẫn theo ID: {e}")
            return None

    def _model_to_dict(self, guide: FirstAidGuide) -> Dict[str, Any]:
        """Convert SQLModel to dict."""
        # Extract source string from JSONB
        source_value = None
        if guide.source:
            if isinstance(guide.source, dict):
                source_value = guide.source.get("source")
            elif isinstance(guide.source, str):
                source_value = guide.source
        
        return {
            "firstaidguide_id": str(guide.firstaidguide_id),
            "wound_type": guide.wound_type,
            "severity": guide.severity,
            "sub_type": guide.sub_type,
            "title": guide.title,
            "steps": FirstAidGuide.extract_list(guide.steps),
            "dos": FirstAidGuide.extract_list(guide.dos),
            "donts": FirstAidGuide.extract_list(guide.donts),
            "supplies_needed": FirstAidGuide.extract_list(guide.supplies_needed),
            "source": source_value,
            "estimated_healing_time": guide.estimated_healing_time,
            "is_active": guide.is_active,
            "version": guide.version,
            "created_by": str(guide.created_by) if guide.created_by else None,
            "created_at": guide.created_at,
            "updated_at": guide.updated_at
        }