from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

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
        """
        Lấy first aid guide với support cho sub_type.
        """
        try:
            logger.info(
                f"🔍 Getting first aid guide: wound_type={wound_type}, "
                f"severity={severity}, sub_type={sub_type}"
            )

            # Strategy 1: Tìm guide cụ thể với sub_type
            if sub_type:
                specific_guide = await self._find_guide_specific(wound_type, severity, sub_type)
                if specific_guide:
                    logger.info(f"Found specific guide with sub_type={sub_type}")
                    return self._format_guide_response(specific_guide)

                logger.warning(f"No guide found with sub_type={sub_type}, trying general guide")

            # Strategy 2: Fallback - tìm guide chung (sub_type = NULL hoặc bất kỳ)
            general_guide = await self._find_guide_general(wound_type, severity)

            if general_guide:
                logger.info(f"Found general guide")
                return self._format_guide_response(general_guide)

            logger.warning(f"No guide found for {wound_type}/{severity}")
            return None

        except Exception as e:
            logger.error(f"Error getting first aid guide: {e}", exc_info=True)
            return None

    async def _find_guide_specific(
        self,
        wound_type: str,
        severity: str,
        sub_type: str
    ) -> Optional[Dict[str, Any]]:
        """Tìm guide cụ thể với sub_type."""
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
            logger.error(f"Error finding specific guide: {e}")
            return None

    async def _find_guide_general(
        self,
        wound_type: str,
        severity: str
    ) -> Optional[Dict[str, Any]]:
        """Tìm guide chung (không có sub_type hoặc sub_type rỗng)."""
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
            logger.error(f"Error finding general guide: {e}")
            return None

    def _format_guide_response(self, guide: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format guide thành response dict.
        Sử dụng helper methods từ model để trả về lists thay vì dict.
        """
        # Tạo FirstAidGuide instance tạm thời để sử dụng helper methods
        guide_model = FirstAidGuide(**guide)

        return {
            "firstaidguide_id": guide.get("firstaidguide_id"),
            "wound_type": guide.get("wound_type"),
            "severity": guide.get("severity"),
            "sub_type": guide.get("sub_type"),
            "title": guide.get("title"),
            "description": guide.get("description"),
            "steps": guide_model.get_steps_list(),
            "warnings": guide_model.get_warnings_list(),
            "dos": guide_model.get_dos_list(),
            "donts": guide_model.get_donts_list(),
            "supplies_needed": guide_model.get_supplies_list(),
            "estimated_healing_time": guide.get("estimated_healing_time"),
            "is_active": guide.get("is_active"),
            "version": guide.get("version"),
            "created_by": guide.get("created_by"),
            "created_at": guide.get("created_at"),
            "updated_at": guide.get("updated_at")
        }

    def _parse_instructions(self, instructions_text: str) -> List[str]:
        if not instructions_text:
            return []

        instructions = []
        for line in instructions_text.split('\n'):
            line = line.strip()
            if line:
                if line[0].isdigit() and '. ' in line[:4]:
                    line = line.split('. ', 1)[1]
                instructions.append(line)

        return instructions

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

                wound_types[wound_type]["severities"].append(severity)

            return list(wound_types.values())

        except Exception as e:
            logger.error(f"Failed to get available wound types: {e}")
            return []

    async def search_first_aid_guides(
        self,
        wound_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        try:
            where_conditions = []
            params = {"limit": limit}

            if wound_type:
                where_conditions.append("wound_type = :wound_type")
                params["wound_type"] = wound_type

            if severity:
                where_conditions.append("severity = :severity")
                params["severity"] = severity

            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            sql = text(f"""
                SELECT * FROM firstaid_guides
                WHERE is_active = true {where_clause.replace('WHERE', 'AND') if where_clause else ''}
                ORDER BY wound_type, severity
                LIMIT :limit
            """)

            result = await self.db.execute(sql, params)
            rows = result.mappings().all()

            guides = []
            for row in rows:
                guide = dict(row)
                guides.append(self._format_guide_response(guide))

            logger.info(f"Found {len(guides)} first aid guides")
            return guides

        except Exception as e:
            logger.error(f"Failed to search first aid guides: {e}")
            return []
        
    async def create_first_aid_guide(
        self,
        wound_type: str,
        severity: str,
        title: str,
        description: Optional[str] = None,
        steps: Optional[Dict[str, Any]] = None,
        warnings: Optional[Dict[str, Any]] = None,
        dos: Optional[Dict[str, Any]] = None,
        donts: Optional[Dict[str, Any]] = None,
        supplies_needed: Optional[Dict[str, Any]] = None,
        estimated_healing_time: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Optional[FirstAidGuide]:
        """Create a new first aid guide using ORM."""
        try:
            guide = FirstAidGuide.create_guide(
                wound_type=wound_type,
                severity=severity,
                title=title,
                description=description,
                steps=steps,
                warnings=warnings,
                dos=dos,
                donts=donts,
                supplies_needed=supplies_needed,
                estimated_healing_time=estimated_healing_time,
                created_by=created_by
            )

            self.db.add(guide)
            await self.db.commit()
            await self.db.refresh(guide)

            logger.info(
                f"Created first aid guide using ORM for {wound_type}/{severity}",
                extra={
                    "wound_type": wound_type,
                    "severity": severity,
                    "guide_id": guide.firstaidguide_id
                }
            )

            return guide

        except Exception as e:
            logger.error(f"Failed to create first aid guide using ORM: {e}")
            await self.db.rollback()
            return None

    async def get_guide_statistics(self) -> Dict[str, Any]:
        """Lấy thống kê về first aid knowledge base."""
        try:
            total_query = "SELECT COUNT(*) as total FROM firstaid_guides WHERE is_active = true"
            total_result = await self.db.execute(total_query)
            total_guides = total_result.scalar()

            type_query = """
                SELECT wound_type, COUNT(*) as count
                FROM firstaid_guides
                WHERE is_active = true
                GROUP BY wound_type
                ORDER BY count DESC
            """
            type_result = await self.db.execute(type_query)
            type_stats = type_result.fetchall()

            severity_query = """
                SELECT severity, COUNT(*) as count
                FROM firstaid_guides
                WHERE is_active = true
                GROUP BY severity
                ORDER BY count DESC
            """
            severity_result = await self.db.execute(severity_query)
            severity_stats = severity_result.fetchall()

            return {
                "total_guides": total_guides,
                "wound_type_breakdown": {row.wound_type: row.count for row in type_stats},
                "severity_breakdown": {row.severity: row.count for row in severity_stats},
                "coverage_percentage": min(100, (total_guides / 15) * 100) 
            }

        except Exception as e:
            logger.error(f"Failed to get guide statistics: {e}")
            return {
                "total_guides": 0,
                "wound_type_breakdown": {},
                "severity_breakdown": {},
                "coverage_percentage": 0
            }

    async def validate_guide_completeness(self, guide_data: Dict[str, Any]) -> Dict[str, Any]:
        """Kiểm tra tính đầy đủ của first aid guide."""
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

    async def get_recommended_guides_for_wound_types(self, wound_types: List[str]) -> Dict[str, Any]:
        """Lấy các guides được khuyến nghị cho các loại vết thương."""
        try:
            essential_wound_types = ["scratch", "bruise", "burn", "cut", "wound"]

            recommendations = {}
            for wound_type in essential_wound_types:
                if wound_type in wound_types:
                    # Đã có hướng dẫn
                    recommendations[wound_type] = "available"
                else:
                    # Thiếu hướng dẫn
                    recommendations[wound_type] = "missing"

            return {
                "essential_coverage": recommendations,
                "coverage_percentage": (len([r for r in recommendations.values() if r == "available"]) / len(recommendations)) * 100,
                "missing_guides": [wt for wt, status in recommendations.items() if status == "missing"]
            }

        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return {
                "essential_coverage": {},
                "coverage_percentage": 0,
                "missing_guides": []
            }