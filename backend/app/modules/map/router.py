from fastapi import APIRouter, HTTPException, Query
from app.modules.map import services
from app.modules.map.schemas import NearbyPlacesResponse, GeocodeResponse

router = APIRouter(prefix="/map", tags=["Map"])

@router.get("/nearby", response_model=NearbyPlacesResponse)
async def find_nearby_places(
    lat: float = Query(..., description="Latitude of the user"),
    lon: float = Query(..., description="Longitude of the user"),
    type: str = Query("hospital", enum=["hospital", "pharmacy", "all"])
):
    categories = "healthcare.hospital"
    if type == "pharmacy":
        categories = "healthcare.pharmacy"
    elif type == "all":
        categories = "healthcare.hospital,healthcare.pharmacy"

    try:
        places = await services.get_nearby_places(lat, lon, categories)
        return {"places": places}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/geocode", response_model=GeocodeResponse)
async def geocode_address(
    address: str = Query(..., description="Địa chỉ cần tìm kiếm")
):
    try:
        results = await services.geocode_address(address)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))