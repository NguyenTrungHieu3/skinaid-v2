from pydantic import BaseModel, Field, validator
from typing import List, Optional, Tuple

class NearbyPlacesRequest(BaseModel):
    """
    Request để tìm địa điểm gần vị trí
    """
    latitude: float = Field(..., description="Vĩ độ trung tâm", ge=-90, le=90)
    longitude: float = Field(..., description="Kinh độ trung tâm", ge=-180, le=180)
    category: str = Field(
        default="healthcare.hospital",
        description="Loại địa điểm (healthcare.hospital, healthcare.clinic, etc)"
    )
    radius: int = Field(
        default=5000,
        description="Bán kính tìm kiếm (mét)",
        ge=100,
        le=50000
    )
    limit: int = Field(
        default=20,
        description="Số lượng kết quả tối đa",
        ge=1,
        le=50
    )

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 10.762622,
                "longitude": 106.660172,
                "category": "healthcare.hospital",
                "radius": 5000,
                "limit": 20
            }
        }


class RouteRequest(BaseModel):
    """
    Request để tính đường đi từ A → B
    """
    start_latitude: float = Field(..., description="Vĩ độ điểm bắt đầu", ge=-90, le=90)
    start_longitude: float = Field(..., description="Kinh độ điểm bắt đầu", ge=-180, le=180)
    end_latitude: float = Field(..., description="Vĩ độ điểm kết thúc", ge=-90, le=90)
    end_longitude: float = Field(..., description="Kinh độ điểm kết thúc", ge=-180, le=180)
    mode: str = Field(
        default="drive",
        description="Phương thức di chuyển: drive, walk, bike (hoặc driving, walking, bicycling)"
    )

    @validator("mode")
    def validate_mode(cls, v):
        """
        Validate và map mode về format Geoapify.
        Accept cả Google Maps format (driving, walking, bicycling, transit)
        và Geoapify format (drive, walk, bike)
        """
        # Mapping từ các format phổ biến sang Geoapify format
        mode_mapping = {
            # Google Maps style
            "driving": "drive",
            "walking": "walk",
            "bicycling": "bike",
            "transit": "drive",  # Geoapify không có transit, fallback to drive
            # Geoapify style (giữ nguyên)
            "drive": "drive",
            "walk": "walk",
            "bike": "bike"
        }
        
        # Normalize to lowercase
        v_lower = v.lower()
        
        if v_lower not in mode_mapping:
            allowed = list(mode_mapping.keys())
            raise ValueError(
                f"mode phải là một trong: {', '.join(allowed)}"
            )
        
        # Return mapped value
        return mode_mapping[v_lower]

    class Config:
        json_schema_extra = {
            "example": {
                "start_latitude": 10.762622,
                "start_longitude": 106.660172,
                "end_latitude": 10.772622,
                "end_longitude": 106.670172,
                "mode": "drive"
            }
        }


# ============ Response Schemas ============

class LocationResponse(BaseModel):
    """
    Response chứa thông tin vị trí
    """
    latitude: float = Field(..., description="Vĩ độ")
    longitude: float = Field(..., description="Kinh độ")
    city: Optional[str] = Field(None, description="Tên thành phố")
    country: Optional[str] = Field(None, description="Tên quốc gia")
    accuracy: str = Field(..., description="Độ chính xác: gps, ip_based")
    source: str = Field(..., description="Nguồn: gps, ip")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 10.762622,
                "longitude": 106.660172,
                "city": "Ho Chi Minh City",
                "country": "Vietnam",
                "accuracy": "ip_based",
                "source": "ip"
            }
        }


class PlaceResponse(BaseModel):
    """
    Response chứa thông tin một địa điểm
    """
    place_id: str = Field(..., description="ID duy nhất của địa điểm")
    name: str = Field(..., description="Tên địa điểm")
    category: str = Field(..., description="Loại địa điểm")
    latitude: float = Field(..., description="Vĩ độ")
    longitude: float = Field(..., description="Kinh độ")
    address: str = Field(..., description="Địa chỉ đầy đủ")
    distance: float = Field(..., description="Khoảng cách từ vị trí user (mét)")
    phone: Optional[str] = Field(None, description="Số điện thoại")
    opening_hours: Optional[str] = Field(None, description="Giờ mở cửa")
    rating: Optional[float] = Field(None, description="Đánh giá (0-5)")
    website: Optional[str] = Field(None, description="Website")
    marker_icon_url: str = Field(..., description="URL của marker icon")

    class Config:
        json_schema_extra = {
            "example": {
                "place_id": "abc123",
                "name": "Bệnh viện Chợ Rẫy",
                "category": "healthcare.hospital",
                "latitude": 10.754981,
                "longitude": 106.661156,
                "address": "201B Nguyễn Chí Thanh, Quận 5, TP.HCM",
                "distance": 1250.5,
                "phone": "+84 28 3855 4137",
                "opening_hours": "24/7",
                "rating": 4.5,
                "website": "https://choray.vn",
                "marker_icon_url": "https://api.geoapify.com/v1/icon?..."
            }
        }


class RouteStep(BaseModel):
    """
    Một bước trong hướng dẫn đường đi
    """
    instruction: str = Field(..., description="Hướng dẫn (VD: 'Rẽ phải vào Nguyễn Huệ')")
    distance: float = Field(..., description="Khoảng cách bước này (mét)")
    duration: float = Field(..., description="Thời gian dự kiến (giây)")


class RouteResponse(BaseModel):
    """
    Response chứa thông tin route
    """
    distance: float = Field(..., description="Tổng khoảng cách (mét)")
    duration: float = Field(..., description="Tổng thời gian (giây)")
    distance_km: float = Field(..., description="Khoảng cách (km)")
    duration_minutes: float = Field(..., description="Thời gian (phút)")
    mode: str = Field(..., description="Phương thức di chuyển")
    summary: str = Field(..., description="Tóm tắt route")
    geometry: List[List[float]] = Field(
        ...,
        description="Mảng tọa độ [[lat, lon], ...] để vẽ route"
    )
    steps: List[RouteStep] = Field(..., description="Hướng dẫn từng bước")

    class Config:
        json_schema_extra = {
            "example": {
                "distance": 3500,
                "duration": 480,
                "distance_km": 3.5,
                "duration_minutes": 8.0,
                "mode": "drive",
                "summary": "Lái xe: 3.5km, khoảng 8 phút",
                "geometry": [
                    [10.762622, 106.660172],
                    [10.763000, 106.661000],
                    [10.772622, 106.670172]
                ],
                "steps": [
                    {
                        "instruction": "Quẹo phải vào đường Nguyễn Huệ",
                        "distance": 150,
                        "duration": 30
                    }
                ]
            }
        }


class GeocodeResponse(BaseModel):
    """
    Response cho geocoding (địa chỉ → tọa độ)
    """
    latitude: float = Field(..., description="Vĩ độ")
    longitude: float = Field(..., description="Kinh độ")
    formatted_address: str = Field(..., description="Địa chỉ được format")
    place_id: str = Field(..., description="ID địa điểm")
    city: Optional[str] = Field(None, description="Thành phố")
    country: Optional[str] = Field(None, description="Quốc gia")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 10.754981,
                "longitude": 106.661156,
                "formatted_address": "Bệnh viện Chợ Rẫy, 201B Nguyễn Chí Thanh, Quận 5",
                "place_id": "abc123",
                "city": "Ho Chi Minh City",
                "country": "Vietnam"
            }
        }


class ReverseGeocodeResponse(BaseModel):
    """
    Response cho reverse geocoding (tọa độ → địa chỉ)
    """
    formatted_address: str = Field(..., description="Địa chỉ đầy đủ")
    street: Optional[str] = Field(None, description="Tên đường")
    city: Optional[str] = Field(None, description="Thành phố")
    country: Optional[str] = Field(None, description="Quốc gia")
    postcode: Optional[str] = Field(None, description="Mã bưu điện")