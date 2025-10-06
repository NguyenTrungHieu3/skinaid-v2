from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

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
            "id": guide.get("firstaidguides_id"),
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