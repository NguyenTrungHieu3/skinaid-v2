from fastapi import APIRouter, Query, HTTPException, status
from typing import List
import logging

from .controller import map_controller
from .schemas import (
    NearbyPlacesRequest,
    PlaceResponse,
    RouteRequest,
    RouteResponse,
    LocationResponse,
    GeocodeResponse,
    ReverseGeocodeResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/map")


@router.get(
    "/ip-location",
    response_model=LocationResponse,
    summary="Lấy vị trí từ IP",
    description="Xác định vị trí người dùng dựa trên IP address (fallback khi GPS không khả dụng)"
)
async def get_ip_location():
    """
    Lấy vị trí người dùng từ IP address
    """
    logger.info("[MAP_API] GET /ip-location")
    return await map_controller.get_user_location_from_ip()


@router.post(
    "/nearby-places",
    response_model=List[PlaceResponse],
    summary="Tìm địa điểm gần đây",
    description="Tìm các cơ sở y tế (bệnh viện, phòng khám, nhà thuốc) gần vị trí đã cho"
)
async def find_nearby_places(request: NearbyPlacesRequest):
    """
    Tìm các địa điểm gần vị trí người dùng
    """
    logger.info(
        f"[MAP_API] POST /nearby-places: "
        f"category={request.category}, radius={request.radius}m"
    )
    return await map_controller.find_nearby_healthcare_facilities(request)


@router.post(
    "/route",
    response_model=RouteResponse,
    summary="Tính đường đi",
    description="Tính toán route từ vị trí hiện tại đến địa điểm đã chọn"
)
async def calculate_route(request: RouteRequest):
    """
    Tính toán route từ điểm A đến điểm B
    """
    logger.info(
        f"[MAP_API] POST /route: "
        f"({request.start_latitude},{request.start_longitude}) → "
        f"({request.end_latitude},{request.end_longitude}), "
        f"mode={request.mode}"
    )
    return await map_controller.calculate_route_to_place(request)


@router.get(
    "/geocode",
    response_model=GeocodeResponse,
    summary="Tìm tọa độ từ địa chỉ",
    description="Search địa điểm theo tên hoặc địa chỉ (Geocoding)"
)
async def geocode_address(
    address: str = Query(
        ...,
        description="Địa chỉ hoặc tên địa điểm cần tìm",
        min_length=3,
        example="Bệnh viện Chợ Rẫy, TP.HCM"
    )
):
    """
    Tìm tọa độ từ địa chỉ text (Geocoding)
    """
    logger.info(f"[MAP_API] GET /geocode: address={address}")
    return await map_controller.geocode_search(address)


@router.get(
    "/reverse-geocode",
    response_model=ReverseGeocodeResponse,
    summary="Chuyển tọa độ thành địa chỉ",
    description="Reverse geocoding: tìm địa chỉ từ tọa độ"
)
async def reverse_geocode(
    latitude: float = Query(..., description="Vĩ độ", ge=-90, le=90),
    longitude: float = Query(..., description="Kinh độ", ge=-180, le=180)
):
    """
    Chuyển tọa độ thành địa chỉ (Reverse Geocoding)
    """
    logger.info(
        f"[MAP_API] GET /reverse-geocode: ({latitude}, {longitude})"
    )
    result = await map_controller.reverse_geocode_location(latitude, longitude)
    return ReverseGeocodeResponse(**result)