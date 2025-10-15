from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlmodel import select
import logging

from app.modules.firstaid.models.firstaid_guide import FirstAidGuide

logger = logging.getLogger(__name__)

class FirstAidService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_first_aid_guide(
        self,
        wound_type: str,
        severity: str
    ) -> Optional[Dict[str, Any]]:
        try:
            sql = text("""
                SELECT *
                FROM firstaidguides
                WHERE wound_type = :wound_type AND severity = :severity
                LIMIT 1
            """)

            result = await self.db.execute(sql, {
                "wound_type": wound_type,
                "severity": severity
            })

            row = result.mappings().first()

            if not row:
                logger.warning(
                    f"No first aid guide found for {wound_type}/{severity}",
                    extra={
                        "wound_type": wound_type,
                        "severity": severity
                    }
                )
                return None

            guide = dict(row)

            logger.info(
                f"Found first aid guide for {wound_type}/{severity}",
                extra={
                    "wound_type": wound_type,
                    "severity": severity,
                    "guide_id": guide.get("firstaidguides_id")
                }
            )

            return self._format_guide_response(guide)

        except Exception as e:
            logger.error(
                f"Failed to get first aid guide: {e}",
                extra={
                    "wound_type": wound_type,
                    "severity": severity,
                    "error": str(e)
                }
            )
            return None

    def _format_guide_response(self, guide: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "firstaidguides_id": guide.get("firstaidguides_id"),
            "wound_type": guide.get("wound_type"),
            "severity": guide.get("severity"),
            "information": {
                "cause": guide.get("cause"),
                "symptoms": guide.get("symptoms"),
                "risks": guide.get("risks")
            },
            "instructions": {
                "do": self._parse_instructions(guide.get("first_aid_do", "")),
                "dont": self._parse_instructions(guide.get("first_aid_dont", ""))
            },
            "tip": guide.get("tip_easy_remember"),
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
                FROM firstaidguides
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
                SELECT * FROM firstaidguides
                {where_clause}
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

    # === ORM-based methods (improved versions) ===

    async def get_first_aid_guide_orm(
        self,
        wound_type: str,
        severity: str
    ) -> Optional[FirstAidGuide]:
        """Get first aid guide using ORM (improved version)."""
        try:
            statement = select(FirstAidGuide).where(
                FirstAidGuide.wound_type == wound_type,
                FirstAidGuide.severity == severity
            )
            result = await self.db.execute(statement)
            guide = result.scalar_one_or_none()

            if guide:
                logger.info(
                    f"Found first aid guide using ORM for {wound_type}/{severity}",
                    extra={
                        "wound_type": wound_type,
                        "severity": severity,
                        "guide_id": guide.firstaidguides_id
                    }
                )
            else:
                logger.warning(
                    f"No first aid guide found using ORM for {wound_type}/{severity}",
                    extra={
                        "wound_type": wound_type,
                        "severity": severity
                    }
                )

            return guide

        except Exception as e:
            logger.error(
                f"Failed to get first aid guide using ORM: {e}",
                extra={
                    "wound_type": wound_type,
                    "severity": severity,
                    "error": str(e)
                }
            )
            return None

    async def create_first_aid_guide(
        self,
        wound_type: str,
        severity: str,
        cause: Optional[str] = None,
        symptoms: Optional[str] = None,
        risks: Optional[str] = None,
        first_aid_do: Optional[str] = None,
        first_aid_dont: Optional[str] = None,
        tip_easy_remember: Optional[str] = None
    ) -> Optional[FirstAidGuide]:
        """Create a new first aid guide using ORM."""
        try:
            guide = FirstAidGuide.create_guide(
                wound_type=wound_type,
                severity=severity,
                cause=cause,
                symptoms=symptoms,
                risks=risks,
                first_aid_do=first_aid_do,
                first_aid_dont=first_aid_dont,
                tip_easy_remember=tip_easy_remember
            )

            self.db.add(guide)
            await self.db.commit()
            await self.db.refresh(guide)

            logger.info(
                f"Created first aid guide using ORM for {wound_type}/{severity}",
                extra={
                    "wound_type": wound_type,
                    "severity": severity,
                    "guide_id": guide.firstaidguides_id
                }
            )

            return guide

        except Exception as e:
            logger.error(f"Failed to create first aid guide using ORM: {e}")
            await self.db.rollback()
            return None

    async def get_available_wound_types_orm(self) -> List[Dict[str, Any]]:
        """Get available wound types using ORM (improved version)."""
        try:
            statement = select(FirstAidGuide.wound_type, FirstAidGuide.severity).distinct()
            result = await self.db.execute(statement)
            rows = result.all()

            wound_types = {}
            for row in rows:
                wound_type = row.wound_type
                severity = row.severity

                if wound_type not in wound_types:
                    wound_types[wound_type] = {
                        "wound_type": wound_type,
                        "severities": []
                    }

                wound_types[wound_type]["severities"].append(severity)

            return list(wound_types.values())

        except Exception as e:
            logger.error(f"Failed to get available wound types using ORM: {e}")
            return []