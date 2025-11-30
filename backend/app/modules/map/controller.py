
import logging
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
import httpx

from .service import geoapify_service
from .schemas import (
    NearbyPlacesRequest,
    PlaceResponse,
    RouteRequest,
    RouteResponse,
    LocationResponse,
    GeocodeResponse
)

logger = logging.getLogger(__name__)


class MapController:

    def __init__(self):
        self.service = geoapify_service

    async def get_user_location_from_ip(self) -> LocationResponse:
        try:
            logger.info("[MAP_CONTROLLER] Đang lấy vị trí từ IP...")

            # Gọi service để lấy IP location
            location_data = await self.service.get_ip_location()

            # Validate response
            if not location_data or "latitude" not in location_data:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Không thể xác định vị trí từ IP"
                )

            # Transform to response schema
            response = LocationResponse(
                latitude=location_data["latitude"],
                longitude=location_data["longitude"],
                city=location_data["city"],
                country=location_data["country"],
                accuracy=location_data["accuracy"],
                source="ip"
            )

            logger.info(
                f"[MAP_CONTROLLER] Vị trí IP: "
                f"{response.city}, {response.country}"
            )

            return response

        except httpx.HTTPError as e:
            logger.error(f"[MAP_CONTROLLER] Lỗi Geoapify API: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Dịch vụ định vị tạm thời không khả dụng"
            )
        except Exception as e:
            logger.error(f"[MAP_CONTROLLER] Lỗi không xác định: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Lỗi hệ thống khi xác định vị trí"
            )

    async def find_nearby_healthcare_facilities(
        self,
        request: NearbyPlacesRequest
    ) -> List[PlaceResponse]:
        try:
            logger.info(
                f"[MAP_CONTROLLER] Tìm kiếm địa điểm: "
                f"category={request.category}, "
                f"radius={request.radius}m"
            )

            # Validate radius (không cho phép quá 50km)
            if request.radius > 50000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bán kính tìm kiếm tối đa 50km"
                )

            # Validate coordinates
            if not (-90 <= request.latitude <= 90):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Latitude không hợp lệ (phải từ -90 đến 90)"
                )

            if not (-180 <= request.longitude <= 180):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Longitude không hợp lệ (phải từ -180 đến 180)"
                )

            # Gọi service để tìm địa điểm
            places_data = await self.service.find_nearby_places(
                latitude=request.latitude,
                longitude=request.longitude,
                category=request.category,
                radius=request.radius,
                limit=request.limit
            )

            # Transform mỗi place thành PlaceResponse
            places = []
            for place_data in places_data:
                # Tạo marker icon URL dựa trên category
                icon_url = self._get_icon_for_category(place_data["category"])

                place = PlaceResponse(
                    place_id=place_data["place_id"],
                    name=place_data["name"],
                    category=place_data["category"],
                    latitude=place_data["latitude"],
                    longitude=place_data["longitude"],
                    address=place_data["address"],
                    distance=place_data["distance"],
                    phone=place_data.get("phone"),
                    opening_hours=place_data.get("opening_hours"),
                    rating=place_data.get("rating"),
                    website=place_data.get("website"),
                    marker_icon_url=icon_url
                )
                places.append(place)

            logger.info(
                f"[MAP_CONTROLLER] Tìm thấy {len(places)} địa điểm"
            )

            # Sort by distance (gần nhất trước)
            places.sort(key=lambda p: p.distance)

            return places

        except HTTPException:
            # Re-raise HTTPException đã được raise ở trên
            raise
        except httpx.HTTPError as e:
            logger.error(f"[MAP_CONTROLLER] Lỗi Geoapify API: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Dịch vụ tìm kiếm địa điểm tạm thời không khả dụng"
            )
        except Exception as e:
            logger.error(f"[MAP_CONTROLLER] Lỗi không xác định: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Lỗi hệ thống khi tìm kiếm địa điểm"
            )

    async def calculate_route_to_place(
        self,
        request: RouteRequest
    ) -> RouteResponse:
        try:
            logger.info(
                f"[MAP_CONTROLLER] Tính route: "
                f"({request.start_latitude},{request.start_longitude}) → "
                f"({request.end_latitude},{request.end_longitude}), "
                f"mode={request.mode}"
            )

            # Validate mode
            valid_modes = ["drive", "walk", "bike"]
            if request.mode not in valid_modes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Mode không hợp lệ. Chọn một trong: {', '.join(valid_modes)}"
                )

            # Gọi service để tính route
            route_data = await self.service.calculate_route(
                start_lat=request.start_latitude,
                start_lon=request.start_longitude,
                end_lat=request.end_latitude,
                end_lon=request.end_longitude,
                mode=request.mode
            )

            # Kiểm tra nếu không tìm thấy route
            if not route_data["geometry"]:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Không tìm thấy đường đi giữa hai điểm"
                )

            # Transform to response
            response = RouteResponse(
                distance=route_data["distance"],
                duration=route_data["duration"],
                geometry=route_data["geometry"],
                steps=route_data["steps"],
                mode=route_data["mode"],
                # Format thông tin cho user
                distance_km=round(route_data["distance"] / 1000, 2),
                duration_minutes=round(route_data["duration"] / 60, 1),
                summary=self._format_route_summary(
                    route_data["distance"],
                    route_data["duration"],
                    route_data["mode"]
                )
            )

            logger.info(
                f"[MAP_CONTROLLER] Route tìm thấy: "
                f"{response.distance_km}km, {response.duration_minutes}min"
            )

            return response

        except HTTPException:
            raise
        except httpx.HTTPError as e:
            logger.error(f"[MAP_CONTROLLER] Lỗi Geoapify API: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Dịch vụ tính đường đi tạm thời không khả dụng"
            )
        except Exception as e:
            logger.error(f"[MAP_CONTROLLER] Lỗi không xác định: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Lỗi hệ thống khi tính đường đi"
            )

    async def geocode_search(self, address: str) -> GeocodeResponse:
        try:
            logger.info(f"[MAP_CONTROLLER] Geocoding: {address}")

            # Validate address
            if not address or len(address.strip()) < 3:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Địa chỉ phải có ít nhất 3 ký tự"
                )

            # Gọi service
            result = await self.service.geocode_address(address.strip())

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy địa chỉ: {address}"
                )

            response = GeocodeResponse(
                latitude=result["latitude"],
                longitude=result["longitude"],
                formatted_address=result["formatted_address"],
                place_id=result["place_id"],
                city=result.get("city"),
                country=result.get("country")
            )

            logger.info(
                f"[MAP_CONTROLLER] Tìm thấy: {response.formatted_address}"
            )

            return response

        except HTTPException:
            raise
        except httpx.HTTPError as e:
            logger.error(f"[MAP_CONTROLLER] Lỗi Geoapify API: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Dịch vụ tìm kiếm địa chỉ tạm thời không khả dụng"
            )
        except Exception as e:
            logger.error(f"[MAP_CONTROLLER] Lỗi không xác định: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Lỗi hệ thống khi tìm kiếm địa chỉ"
            )

    async def reverse_geocode_location(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        try:
            logger.info(
                f"[MAP_CONTROLLER] Reverse geocode: ({latitude}, {longitude})"
            )

            result = await self.service.reverse_geocode(latitude, longitude)

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Không tìm thấy địa chỉ cho tọa độ này"
                )

            logger.info(
                f"[MAP_CONTROLLER] Địa chỉ: {result['formatted_address']}"
            )

            return result

        except HTTPException:
            raise
        except httpx.HTTPError as e:
            logger.error(f"[MAP_CONTROLLER] Lỗi Geoapify API: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Dịch vụ reverse geocoding tạm thời không khả dụng"
            )
        except Exception as e:
            logger.error(f"[MAP_CONTROLLER] Lỗi không xác định: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Lỗi hệ thống khi xử lý reverse geocoding"
            )


    def _get_icon_for_category(self, category: str) -> str:
        # Map category -> (icon_name, color)
        icon_map = {
            "healthcare.hospital": ("hospital", "16a34a"),  # Green
            "healthcare.clinic": ("clinic-medical", "3b82f6"),  # Blue
            "healthcare.pharmacy": ("prescription-bottle", "f97316"),  # Orange
            "healthcare.dentist": ("tooth", "8b5cf6"),  # Purple
            "healthcare.doctors": ("user-md", "0ea5e9"),  # Sky blue
        }

        # Default nếu không match
        icon_name, color = icon_map.get(
            category,
            ("hospital", "dc2626")  # Red default
        )

        return self.service.get_marker_icon_url(
            icon=icon_name,
            color=color,
            size="medium",
            icon_type="awesome"
        )

    def _format_route_summary(
        self,
        distance: float,
        duration: float,
        mode: str
    ) -> str:
        distance_km = round(distance / 1000, 2)
        duration_min = round(duration / 60)

        mode_vn = {
            "drive": "Lái xe",
            "walk": "Đi bộ",
            "bike": "Đạp xe"
        }

        mode_text = mode_vn.get(mode, mode)

        return f"{mode_text}: {distance_km}km, khoảng {duration_min} phút"


map_controller = MapController()