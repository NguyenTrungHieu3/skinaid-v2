from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text
import logging
import uuid

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
                f"Đang lấy hướng dẫn sơ cứu: wound_type={wound_type}, "
                f"severity={severity}, sub_type={sub_type}"
            )

            if sub_type:
                specific_guide = await self._find_guide_specific(
                    wound_type, severity, sub_type
                )
                if specific_guide:
                    logger.info(f"Tìm thấy hướng dẫn cụ thể với sub_type={sub_type}")
                    return self._format_guide_response(specific_guide)

                logger.warning(
                    f"Không tìm thấy hướng dẫn với sub_type={sub_type}, thử hướng dẫn chung"
                )

            general_guide = await self._find_guide_general(wound_type, severity)

            if general_guide:
                logger.info("Tìm thấy hướng dẫn chung")
                return self._format_guide_response(general_guide)

            logger.warning(f"Không tìm thấy hướng dẫn cho {wound_type}/{severity}")
            return None

        except Exception as e:
            logger.error(f"Lỗi khi lấy hướng dẫn sơ cứu: {e}", exc_info=True)
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
                WHERE wound_type = :wound_type
                  AND severity = :severity
                  AND sub_type = :sub_type
                  AND is_active = true
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
            logger.error(f"Lỗi khi tìm hướng dẫn cụ thể: {e}")
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
                WHERE wound_type = :wound_type
                  AND severity = :severity
                  AND is_active = true
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
            logger.error(f"Lỗi khi tìm hướng dẫn chung: {e}")
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
            "description": guide.get("description"),
            "steps": FirstAidGuide.extract_list(guide.get("steps")),
            "warnings": FirstAidGuide.extract_list(guide.get("warnings")),
            "dos": FirstAidGuide.extract_list(guide.get("dos")),
            "donts": FirstAidGuide.extract_list(guide.get("donts")),
            "supplies_needed": FirstAidGuide.extract_list(guide.get("supplies_needed")),
            "estimated_healing_time": guide.get("estimated_healing_time"),
            "is_active": guide.get("is_active"),
            "version": guide.get("version"),
            "created_by": str(created_by_str) if created_by_str else None,
            "created_at": guide.get("created_at"),
            "updated_at": guide.get("updated_at")
        }

    async def get_available_wound_types(self) -> List[Dict[str, Any]]:
        try:
            sql = text("""
                SELECT DISTINCT wound_type, severity
                FROM firstaid_guides
                WHERE is_active = true
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
            logger.error(f"Không thể lấy các loại vết thương có sẵn: {e}")
            return []

    async def search_first_aid_guides(
        self,
        wound_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        try:
            where_conditions = ["is_active = true"]
            params = {"limit": limit}

            if wound_type:
                where_conditions.append("wound_type = :wound_type")
                params["wound_type"] = wound_type

            if severity:
                where_conditions.append("severity = :severity")
                params["severity"] = severity

            where_clause = " AND ".join(where_conditions)

            sql = text(f"""
                SELECT * FROM firstaid_guides
                WHERE {where_clause}
                ORDER BY wound_type, severity
                LIMIT :limit
            """)

            result = await self.db.execute(sql, params)
            rows = result.mappings().all()

            guides = []
            for row in rows:
                guide = dict(row)
                guides.append(self._format_guide_response(guide))

            logger.info(f"Tìm thấy {len(guides)} hướng dẫn sơ cứu")
            return guides

        except Exception as e:
            logger.error(f"Không thể tìm kiếm hướng dẫn sơ cứu: {e}")
            return []

    async def get_guide_statistics(self) -> Dict[str, Any]:
        try:
            total_query = text("""
                SELECT COUNT(*) as total 
                FROM firstaid_guides 
                WHERE is_active = true
            """)
            total_result = await self.db.execute(total_query)
            total_guides = total_result.scalar()

            type_query = text("""
                SELECT wound_type, COUNT(*) as count
                FROM firstaid_guides
                WHERE is_active = true
                GROUP BY wound_type
                ORDER BY count DESC
            """)
            type_result = await self.db.execute(type_query)
            type_stats = type_result.mappings().all()

            severity_query = text("""
                SELECT severity, COUNT(*) as count
                FROM firstaid_guides
                WHERE is_active = true
                GROUP BY severity
                ORDER BY count DESC
            """)
            severity_result = await self.db.execute(severity_query)
            severity_stats = severity_result.mappings().all()

            return {
                "total_guides": total_guides,
                "wound_type_breakdown": {
                    row["wound_type"]: row["count"] for row in type_stats
                },
                "severity_breakdown": {
                    row["severity"]: row["count"] for row in severity_stats
                },
                "coverage_percentage": min(100, (total_guides / 15) * 100)
            }

        except Exception as e:
            logger.error(f"Không thể lấy thống kê hướng dẫn: {e}")
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
                issues.append(f"Missing required field: {field}")

        if not guide_data.get("steps"):
            issues.append("Missing steps information")

        if not guide_data.get("dos"):
            issues.append("Missing 'dos' (things to do)")

        if not guide_data.get("donts"):
            issues.append("Missing 'donts' (things not to do)")

        if guide_data.get("severity") == "severe" and not guide_data.get("warnings"):
            issues.append("Severe wounds should have warnings")

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
            # Convert lists to JSONB format
            steps_jsonb = {"items": guide_data.get("steps", [])}
            warnings_jsonb = {"items": guide_data.get("warnings", [])} if guide_data.get("warnings") else None
            dos_jsonb = {"items": guide_data.get("dos", [])} if guide_data.get("dos") else None
            donts_jsonb = {"items": guide_data.get("donts", [])} if guide_data.get("donts") else None
            supplies_jsonb = {"items": guide_data.get("supplies_needed", [])} if guide_data.get("supplies_needed") else None

            guide = FirstAidGuide.create_guide(
                wound_type=guide_data["wound_type"],
                severity=guide_data["severity"],
                title=guide_data["title"],
                description=guide_data.get("description"),
                sub_type=guide_data.get("sub_type"),
                steps=steps_jsonb,
                warnings=warnings_jsonb,
                dos=dos_jsonb,
                donts=donts_jsonb,
                supplies_needed=supplies_jsonb,
                estimated_healing_time=guide_data.get("estimated_healing_time"),
                created_by=str(created_by) if created_by else None
            )

            self.db.add(guide)
            await self.db.commit()
            await self.db.refresh(guide)

            logger.info(f"Đã tạo hướng dẫn sơ cứu: {guide.firstaidguide_id}")
            
            # Convert to dict for response
            return self._model_to_dict(guide)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Không thể tạo hướng dẫn sơ cứu: {e}", exc_info=True)
            raise

    async def update_first_aid_guide(
        self,
        guide_id: uuid.UUID,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Cập nhật hướng dẫn sơ cứu."""
        try:
            # Find existing guide
            sql = text("""
                SELECT * FROM firstaid_guides
                WHERE firstaidguide_id = :guide_id
            """)
            
            result = await self.db.execute(sql, {"guide_id": guide_id})
            existing_guide = result.mappings().first()
            
            if not existing_guide:
                logger.warning(f"Không tìm thấy hướng dẫn: {guide_id}")
                return None

            # Prepare update fields
            update_fields = []
            params = {"guide_id": guide_id}
            
            if "title" in update_data:
                update_fields.append("title = :title")
                params["title"] = update_data["title"]
            
            if "description" in update_data:
                update_fields.append("description = :description")
                params["description"] = update_data["description"]
            
            if "steps" in update_data:
                update_fields.append("steps = :steps")
                params["steps"] = {"items": update_data["steps"]}
            
            if "warnings" in update_data:
                update_fields.append("warnings = :warnings")
                params["warnings"] = {"items": update_data["warnings"]} if update_data["warnings"] else None
            
            if "dos" in update_data:
                update_fields.append("dos = :dos")
                params["dos"] = {"items": update_data["dos"]} if update_data["dos"] else None
            
            if "donts" in update_data:
                update_fields.append("donts = :donts")
                params["donts"] = {"items": update_data["donts"]} if update_data["donts"] else None
            
            if "supplies_needed" in update_data:
                update_fields.append("supplies_needed = :supplies_needed")
                params["supplies_needed"] = {"items": update_data["supplies_needed"]} if update_data["supplies_needed"] else None
            
            if "estimated_healing_time" in update_data:
                update_fields.append("estimated_healing_time = :estimated_healing_time")
                params["estimated_healing_time"] = update_data["estimated_healing_time"]
            
            if "is_active" in update_data:
                update_fields.append("is_active = :is_active")
                params["is_active"] = update_data["is_active"]
            
            if not update_fields:
                logger.warning("Không có trường nào để cập nhật")
                return dict(existing_guide)
            
            # Add updated_at
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_fields.append("version = version + 1")
            
            # Execute update
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

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Không thể cập nhật hướng dẫn sơ cứu: {e}", exc_info=True)
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
                # Soft delete - chỉ set is_active = false
                sql = text("""
                    UPDATE firstaid_guides
                    SET is_active = false, updated_at = CURRENT_TIMESTAMP
                    WHERE firstaidguide_id = :guide_id
                    RETURNING firstaidguide_id
                """)
            
            result = await self.db.execute(sql, {"guide_id": guide_id})
            deleted = result.mappings().first()
            
            if not deleted:
                logger.warning(f"Không tìm thấy hướng dẫn để xóa: {guide_id}")
                return False
            
            await self.db.commit()
            
            delete_type = "hard" if hard_delete else "soft"
            logger.info(f"Đã {delete_type} xóa hướng dẫn sơ cứu: {guide_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Không thể xóa hướng dẫn sơ cứu: {e}", exc_info=True)
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
            logger.error(f"Không thể lấy hướng dẫn theo ID: {e}")
            return None

    def _model_to_dict(self, guide: FirstAidGuide) -> Dict[str, Any]:
        """Convert SQLModel to dict."""
        return {
            "firstaidguide_id": str(guide.firstaidguide_id),
            "wound_type": guide.wound_type,
            "severity": guide.severity,
            "sub_type": guide.sub_type,
            "title": guide.title,
            "description": guide.description,
            "steps": FirstAidGuide.extract_list(guide.steps),
            "warnings": FirstAidGuide.extract_list(guide.warnings),
            "dos": FirstAidGuide.extract_list(guide.dos),
            "donts": FirstAidGuide.extract_list(guide.donts),
            "supplies_needed": FirstAidGuide.extract_list(guide.supplies_needed),
            "estimated_healing_time": guide.estimated_healing_time,
            "is_active": guide.is_active,
            "version": guide.version,
            "created_by": str(guide.created_by) if guide.created_by else None,
            "created_at": guide.created_at,
            "updated_at": guide.updated_at
        }