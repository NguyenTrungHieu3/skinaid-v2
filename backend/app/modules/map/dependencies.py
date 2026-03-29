from typing import Annotated

from fastapi import Depends

from app.modules.map.service import MapService


def get_map_service() -> MapService:
    return MapService()


MapSvc = Annotated[MapService, Depends(get_map_service)]
