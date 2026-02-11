from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.firstaid.models.firstaid_guide import FirstAidGuide
from app.shared.base_repository import BaseRepository


class FirstAidRepository(BaseRepository[FirstAidGuide]):
    def __init__(self, db: AsyncSession):
        super().__init__(FirstAidGuide, db)

    async def get_specific_guide(
        self, wound_type: str, severity: str, sub_type: str
    ) -> Optional[FirstAidGuide]:
        """Tìm guide cụ thể khớp cả wound_type, severity và sub_type."""
        stmt = (
            select(FirstAidGuide)
            .where(
                func.lower(FirstAidGuide.wound_type) == func.lower(wound_type),
                func.lower(FirstAidGuide.severity) == func.lower(severity),
                func.lower(FirstAidGuide.sub_type) == func.lower(sub_type),
                FirstAidGuide.is_active == True,
                FirstAidGuide.is_deleted == False,
            )
            .order_by(desc(FirstAidGuide.version))
            .limit(1)
        )
        return await self.get_one_by_stmt(stmt)

    async def get_general_guide(
        self, wound_type: str, severity: str
    ) -> Optional[FirstAidGuide]:
        """Tìm guide chung (không có sub_type)."""
        stmt = (
            select(FirstAidGuide)
            .where(
                func.lower(FirstAidGuide.wound_type) == func.lower(wound_type),
                func.lower(FirstAidGuide.severity) == func.lower(severity),
                FirstAidGuide.is_active == True,
                FirstAidGuide.is_deleted == False,
                or_(
                    FirstAidGuide.sub_type.is_(None),
                    FirstAidGuide.sub_type == "",
                ),
            )
            .order_by(desc(FirstAidGuide.version))
            .limit(1)
        )
        return await self.get_one_by_stmt(stmt)

    async def check_duplicate_active(
        self,
        wound_type: str,
        severity: str,
        sub_type: Optional[str],
        exclude_id: Optional[Any] = None,
    ) -> bool:
        """Check nếu đã có guide active khác tồn tại."""
        conditions = [
            func.lower(FirstAidGuide.wound_type) == func.lower(wound_type),
            func.lower(FirstAidGuide.severity) == func.lower(severity),
            FirstAidGuide.is_active == True,
            FirstAidGuide.is_deleted == False,
        ]

        if sub_type:
            conditions.append(
                func.lower(FirstAidGuide.sub_type) == func.lower(sub_type)
            )
        else:
            conditions.append(
                or_(
                    FirstAidGuide.sub_type.is_(None),
                    FirstAidGuide.sub_type == "",
                )
            )

        if exclude_id:
            conditions.append(FirstAidGuide.firstaidguide_id != exclude_id)

        stmt = select(FirstAidGuide).where(and_(*conditions)).limit(1)
        result = await self.db.execute(stmt)
        return result.scalars().first() is not None

    async def get_available_types(self) -> List[Dict[str, Any]]:
        """Lấy danh sách các loại vết thương có sẵn."""
        stmt = (
            select(FirstAidGuide.wound_type, FirstAidGuide.severity)
            .where(
                FirstAidGuide.is_active == True,
                FirstAidGuide.is_deleted == False,
            )
            .distinct()
            .order_by(FirstAidGuide.wound_type, FirstAidGuide.severity)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        # Group logic (move to service or keep here? keep here is fine for data transform)
        # But repository usually returns entities or raw rows.
        # I'll return raw rows and let service group them.
        # Actually existing service does grouping. I can just return list of (type, severity)
        return rows

    async def search(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        wound_type: Optional[str] = None,
        severity: Optional[str] = None,
        is_active: Optional[bool] = None,
        search_query: Optional[str] = None,
    ) -> Tuple[List[FirstAidGuide], int]:
        """Search với filters và pagination."""
        conditions = [FirstAidGuide.is_deleted == False]

        if wound_type:
            conditions.append(
                func.lower(FirstAidGuide.wound_type) == func.lower(wound_type)
            )
        if severity:
            conditions.append(
                func.lower(FirstAidGuide.severity) == func.lower(severity)
            )
        if is_active is not None:
            conditions.append(FirstAidGuide.is_active == is_active)
        if search_query:
            conditions.append(
                FirstAidGuide.title.ilike(f"%{search_query}%")
            )

        # Count
        count_stmt = (
            select(func.count(FirstAidGuide.firstaidguide_id))
            .where(and_(*conditions))
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Items
        stmt = (
            select(FirstAidGuide)
            .where(and_(*conditions))
            .order_by(
                FirstAidGuide.wound_type,
                FirstAidGuide.severity,
                desc(FirstAidGuide.updated_at),
            )
            .offset(skip)
            .limit(limit)
        )
        items = await self.get_many_by_stmt(stmt)

        return items, total

    async def get_statistics(self) -> Dict[str, Any]:
        """Aggregation queries."""
        # Active count
        active_count_stmt = select(func.count()).where(
            FirstAidGuide.is_active == True, FirstAidGuide.is_deleted == False
        )
        active_guides = (await self.db.execute(active_count_stmt)).scalar() or 0

        # Total (non-deleted)
        total_count_stmt = select(func.count()).where(
            FirstAidGuide.is_deleted == False
        )
        total_guides = (await self.db.execute(total_count_stmt)).scalar() or 0

        # By Type
        type_stmt = (
            select(FirstAidGuide.wound_type, func.count())
            .where(
                FirstAidGuide.is_active == True,
                FirstAidGuide.is_deleted == False
            )
            .group_by(FirstAidGuide.wound_type)
            .order_by(desc(func.count()))
        )
        type_result = (await self.db.execute(type_stmt)).all()

        # By Severity
        sev_stmt = (
            select(FirstAidGuide.severity, func.count())
            .where(
                FirstAidGuide.is_active == True,
                FirstAidGuide.is_deleted == False
            )
            .group_by(FirstAidGuide.severity)
            .order_by(desc(func.count()))
        )
        sev_result = (await self.db.execute(sev_stmt)).all()

        return {
            "total_guides": total_guides,
            "active_guides": active_guides,
            "type_stats": type_result,
            "severity_stats": sev_result,
        }
