import asyncio
import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from sqlalchemy import select
from app.modules.firstaid.models.firstaid_guide import FirstAidGuide

VIETNAMESE_NAMES = {
    "abrasion": "Trầy xước",
    "bruise": "Vết bầm",
    "burn": "Bỏng",
    "cut": "Vết cắt đứt",
    "acne": "Mụn nhọt",
    "fungal": "Nhiễm nấm",
    "psoriasis": "Vẩy nến"
}

SEVERITY_NAMES = {
    "mild": "Nhẹ",
    "moderate": "Trung bình",
    "severe": "Nặng",
    "all": "Mọi cấp độ",
    "general": "Chung"
}

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(FirstAidGuide))
        guides = res.scalars().all()
        for guide in guides:
            if len(guide.title) == 36 and guide.title.count('-') == 4:
                wt_name = VIETNAMESE_NAMES.get(guide.wound_type.lower(), guide.wound_type)
                sv_name = SEVERITY_NAMES.get(guide.severity.lower(), guide.severity)
                new_title = f"Chăm sóc {wt_name} ({sv_name})"
                if guide.sub_type:
                    new_title += f" - {guide.sub_type}"
                guide.title = new_title
                db.add(guide)
                db.add(guide)
        await db.commit()

if __name__ == "__main__":
    asyncio.run(main())
