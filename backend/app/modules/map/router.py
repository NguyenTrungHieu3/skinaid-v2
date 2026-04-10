from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
import httpx

from app.modules.map.dependencies import MapSvc
from app.modules.map.service import MapService
from app.modules.map.schemas.api import (
    LocationResponse,
    NearbyPlacesRequest,
    PlaceResponse,
    RouteRequest,
    RouteResponse,
    GeocodeResponse,
    ReverseGeocodeResponse
)
from app.modules.map.exceptions import MapServiceUnavailableError, LocationNotFoundError
from app.shared.response import SuccessResponse


router = APIRouter(prefix="/map")


@router.get(
    "/location/ip",
    response_model=SuccessResponse[LocationResponse],
    summary="Lấy vị trí từ IP"
)
async def get_user_location_from_ip(
    service: MapSvc
) -> SuccessResponse:
    try:
        location_data = await service.get_ip_location()
        return SuccessResponse(
            message="Lấy vị trí thành công",
            data=LocationResponse(**location_data)
        )
    except httpx.HTTPError as e:
        raise MapServiceUnavailableError("Dịch vụ định vị tạm thời không khả dụng")


@router.post(
    "/nearby-places",
    response_model=SuccessResponse[List[PlaceResponse]],
    summary="Tìm địa điểm lân cận"
)
async def find_nearby_places(
    request: NearbyPlacesRequest,
    service: MapSvc
) -> SuccessResponse:
    try:
        places_data = await service.find_nearby_places(
            latitude=request.latitude,
            longitude=request.longitude,
            category=request.category,
            radius=request.radius,
            limit=request.limit
        )

        places = []
        for p in places_data:
            icon_url = _get_icon_for_category(service, p["category"])

            places.append(PlaceResponse(
                place_id=p["place_id"],
                name=p["name"],
                category=p["category"],
                latitude=p["latitude"],
                longitude=p["longitude"],
                address=p["address"],
                distance=p["distance"],
                phone=p.get("phone"),
                opening_hours=p.get("opening_hours"),
                rating=p.get("rating"),
                website=p.get("website"),
                marker_icon_url=icon_url
            ))

        # Sort by distance
        places.sort(key=lambda x: x.distance)

        return SuccessResponse(
            message=f"Tìm thấy {len(places)} địa điểm",
            data=places
        )
    except httpx.HTTPError:
        raise MapServiceUnavailableError("Dịch vụ tìm kiếm địa điểm lỗi")


@router.post(
    "/route",
    response_model=SuccessResponse[RouteResponse],
    summary="Tính đường đi"
)
async def calculate_route(
    request: RouteRequest,
    service: MapSvc
) -> SuccessResponse:
    try:
        route_data = await service.calculate_route(
            start_lat=request.start_latitude,
            start_lon=request.start_longitude,
            end_lat=request.end_latitude,
            end_lon=request.end_longitude,
            mode=request.mode
        )

        if not route_data.get("geometry"):
            raise LocationNotFoundError("Không tìm thấy đường đi")

        # Format details
        distance = route_data["distance"]
        duration = route_data["duration"]
        mode = route_data["mode"]

        dist_km = round(distance / 1000, 2)
        dur_min = round(duration / 60, 1)

        mode_vn = {
            "drive": "Lái xe",
            "walk": "Đi bộ",
            "bike": "Đạp xe"
        }
        summary = f"{mode_vn.get(mode, mode)}: {dist_km}km, khoảng {int(dur_min)} phút"

        geom = route_data["geometry"]
        steps = []
        for s in route_data["steps"]:
            steps.append({
                "instruction": s["instruction"],
                "distance": s["distance"],
                "duration": s["duration"]
            })

        return SuccessResponse(
            message="Tính đường đi thành công",
            data=RouteResponse(
                distance=distance,
                duration=duration,
                distance_km=dist_km,
                duration_minutes=dur_min,
                mode=mode,
                summary=summary,
                geometry=geom,
                steps=steps
            )
        )
    except LocationNotFoundError:
        raise
    except httpx.HTTPError:
        raise MapServiceUnavailableError("Dịch vụ dẫn đường lỗi")


@router.get(
    "/geocode",
    response_model=SuccessResponse[GeocodeResponse],
    summary="Tìm tọa độ từ địa chỉ"
)
async def geocode_address(
    service: MapSvc,
    address: str = Query(..., min_length=3)
) -> SuccessResponse:
    try:
        result = await service.geocode_address(address)
        if not result:
            raise LocationNotFoundError("Address not found")

        return SuccessResponse(
            message="Tìm tọa độ thành công",
            data=GeocodeResponse(**result)
        )
    except httpx.HTTPError:
        raise MapServiceUnavailableError("Geocoding service unavailable")


@router.get(
    "/reverse-geocode",
    response_model=SuccessResponse[ReverseGeocodeResponse],
    summary="Tìm địa chỉ từ tọa độ"
)
async def reverse_geocode(
    latitude: float,
    longitude: float,
    service: MapSvc
) -> SuccessResponse:
    try:
        result = await service.reverse_geocode(latitude, longitude)
        if not result:
            raise LocationNotFoundError("Location not found")

        return SuccessResponse(
            message="Tìm địa chỉ thành công",
            data=ReverseGeocodeResponse(**result)
        )
    except httpx.HTTPError:
        raise MapServiceUnavailableError("Reverse geocoding service unavailable")


def _get_icon_for_category(service: MapService, category: str) -> str:
    category = category.lower()
    icon_map = {
        "healthcare.hospital": ("hospital", "16a34a"),
        "healthcare.clinic": ("clinic-medical", "3b82f6"),
        "healthcare.pharmacy": ("prescription-bottle", "f97316"),
        "healthcare.dentist": ("tooth", "8b5cf6"),
        "healthcare.doctors": ("user-md", "0ea5e9"),
    }
    icon_name, color = ("hospital", "dc2626")  # Default

    if category in icon_map:
        icon_name, color = icon_map[category]
    else:
        # Fallback logic
        if "hospital" in category:
            icon_name, color = icon_map["healthcare.hospital"]
        elif "clinic" in category:
            icon_name, color = icon_map["healthcare.clinic"]
        elif "pharmacy" in category:
            icon_name, color = icon_map["healthcare.pharmacy"]

    return service.get_marker_icon_url(icon=icon_name, color=color)
