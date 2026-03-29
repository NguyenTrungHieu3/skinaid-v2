from uuid import uuid4, UUID
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.firstaid.exceptions import (
    FirstAidGuideNotFoundError,
    GuideAlreadyExistsError,
    InvalidGuideDataError,
)
from app.modules.firstaid.models.firstaid_guide import FirstAidGuide
from app.modules.firstaid.repository import FirstAidRepository
from app.modules.firstaid.schemas.api import (
    CreateGuideRequest,
    FirstAidGuideResponse,
    GuideStatsResponse,
    GuideValidationResponse,
    UpdateGuideRequest,
)


class FirstAidService:
    def __init__(self, repository: FirstAidRepository, db: AsyncSession):
        self.repository = repository
        self.db = db

    async def get_guide(
        self,
        wound_type: str,
        severity: str,
        sub_type: Optional[str] = None,
    ) -> Optional[FirstAidGuide]:
        if sub_type:
            guide = await self.repository.get_specific_guide(
                wound_type, severity, sub_type
            )
            if guide:
                return guide

            guide = await self.repository.get_general_guide(wound_type, severity)
            return guide

        guide = await self.repository.get_general_guide(wound_type, severity)
        return guide

    async def get_guide_by_id(self, guide_id: UUID) -> FirstAidGuide:
        guide = await self.repository.get_by_id(guide_id)
        if not guide or guide.is_deleted:
            raise FirstAidGuideNotFoundError(str(guide_id))
        return guide

    async def search_guides(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        wound_type: Optional[str] = None,
        severity: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[FirstAidGuide], int]:
        return await self.repository.search(
            skip=skip,
            limit=limit,
            wound_type=wound_type,
            severity=severity,
            is_active=is_active,
            search_query=search,
        )

    async def create_guide(
        self, request: CreateGuideRequest, created_by: Optional[UUID]
    ) -> FirstAidGuide:
        if request.is_active:
            exists = await self.repository.check_duplicate_active(
                request.wound_type, request.severity, request.sub_type
            )
            if exists:
                msg = f"Guide active {request.wound_type}/{request.severity}"
                if request.sub_type:
                    msg += f"/{request.sub_type}"
                msg += " đã tồn tại."
                raise GuideAlreadyExistsError(msg)

        steps_json = {"items": request.steps} if request.steps else None
        dos_json = {"items": request.dos} if request.dos else None
        donts_json = {"items": request.donts} if request.donts else None
        supplies_json = (
            {"items": request.supplies_needed}
            if request.supplies_needed
            else None
        )
        # Convert GuideSource to dict for JSONB storage
        if request.source:
            if hasattr(request.source, 'model_dump'):
                source_json = request.source.model_dump()
            elif isinstance(request.source, dict):
                source_json = request.source
            else:
                source_json = {"name": str(request.source), "url": None}
        else:
            source_json = None

        guide = FirstAidGuide.create_guide(
            wound_type=request.wound_type,
            severity=request.severity,
            title=request.title,
            sub_type=request.sub_type,
            steps=steps_json,
            dos=dos_json,
            donts=donts_json,
            supplies_needed=supplies_json,
            estimated_healing_time=request.estimated_healing_time,
            source=source_json,
            is_active=request.is_active,
            created_by=created_by
        )

        self.db.add(guide)
        await self.db.flush()
        await self.db.refresh(guide)
        return guide

    async def update_guide(
        self, guide_id: UUID, request: UpdateGuideRequest
    ) -> FirstAidGuide:
        guide = await self.repository.get_by_id(guide_id)
        if not guide or guide.is_deleted:
            raise FirstAidGuideNotFoundError(str(guide_id))

        if request.is_active is True and not guide.is_active:
            w_type = request.wound_type or guide.wound_type
            sev = request.severity or guide.severity
            s_type = request.sub_type if request.sub_type is not None else guide.sub_type

            exists = await self.repository.check_duplicate_active(
                w_type, sev, s_type, exclude_id=guide_id
            )
            if exists:
                raise GuideAlreadyExistsError("Active guide conflict")

        update_data = request.model_dump(exclude_unset=True)

        def update_jsonb(field_name, list_val):
            if list_val is not None:
                setattr(guide, field_name, {"items": list_val})

        if "steps" in update_data:
            update_jsonb("steps", update_data["steps"])
        if "dos" in update_data:
            update_jsonb("dos", update_data["dos"])
        if "donts" in update_data:
            update_jsonb("donts", update_data["donts"])
        if "supplies_needed" in update_data:
            update_jsonb("supplies_needed", update_data["supplies_needed"])

        if "source" in update_data:
            val = update_data["source"]
            # Convert GuideSource to dict for JSONB storage
            if val is not None and hasattr(val, 'model_dump'):
                guide.source = val.model_dump()
            elif isinstance(val, dict):
                guide.source = val
            elif isinstance(val, str):
                guide.source = {"name": val, "url": None}
            else:
                guide.source = None

        fields = ["title", "wound_type", "severity",
                  "sub_type", "estimated_healing_time", "is_active"]
        for field in fields:
            if field in update_data:
                setattr(guide, field, update_data[field])

        guide.version += 1

        await self.db.flush()
        await self.db.refresh(guide)
        return guide

    async def delete_guide(self, guide_id: UUID, hard_delete: bool = False) -> bool:
        guide = await self.repository.get_by_id(guide_id)
        if not guide:
            raise FirstAidGuideNotFoundError(str(guide_id))

        if hard_delete:
            await self.repository.delete(guide_id)
        else:
            # Pass entity to soft_delete, not ID
            await self.repository.soft_delete(guide)

        return True

    async def get_stats(self) -> GuideStatsResponse:
        stats = await self.repository.get_statistics()

        coverage = min(100.0, (stats["active_guides"] / 15) * 100)

        w_breakdown = {row[0]: row[1] for row in stats["type_stats"]}
        s_breakdown = {row[0]: row[1] for row in stats["severity_stats"]}

        return GuideStatsResponse(
            total_guides=stats["total_guides"],
            active_guides=stats["active_guides"],
            wound_type_breakdown=w_breakdown,
            severity_breakdown=s_breakdown,
            coverage_percentage=coverage
        )

    async def get_available_types(self) -> List[Dict[str, Any]]:
        rows = await self.repository.get_available_types()
        wound_types = {}
        for row in rows:
            wt = row.wound_type
            sv = row.severity

            if wt not in wound_types:
                wound_types[wt] = {"wound_type": wt, "severities": []}
            if sv not in wound_types[wt]["severities"]:
                wound_types[wt]["severities"].append(sv)

        return list(wound_types.values())

    async def check_availability(
        self, wound_type: str, severity: str, sub_type: Optional[str] = None
    ) -> Dict[str, Any]:
        guide = await self.get_guide(wound_type, severity, sub_type)
        if guide:
            return {
                "available": True,
                "guide_id": guide.firstaidguide_id,
                "sub_type": guide.sub_type,
                "version": guide.version,
                "last_updated": guide.updated_at,
            }

        all_types = await self.get_available_types()
        alternatives = []
        for wt in all_types:
            wt_name = wt["wound_type"]
            for sev in wt.get("severities", []):
                if not (wt_name == wound_type and sev == severity):
                    alternatives.append(f"{wt_name}/{sev}")

        return {
            "available": False,
            "alternatives": alternatives[:5],
            "total_alternatives": len(alternatives)
        }
