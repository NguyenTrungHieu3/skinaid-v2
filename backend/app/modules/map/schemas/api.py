from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class NearbyPlacesRequest(BaseModel):
    """
    Request để tìm địa điểm gần vị trí
    """
    latitude: float = Field(..., description="Vĩ độ trung tâm", ge=-90, le=90)
    longitude: float = Field(...,
                             description="Kinh độ trung tâm", ge=-180, le=180)
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
    start_latitude: float = Field(...,
                                  description="Vĩ độ điểm bắt đầu", ge=-90, le=90)
    start_longitude: float = Field(...,
                                   description="Kinh độ điểm bắt đầu", ge=-180, le=180)
    end_latitude: float = Field(...,
                                description="Vĩ độ điểm kết thúc", ge=-90, le=90)
    end_longitude: float = Field(...,
                                 description="Kinh độ điểm kết thúc", ge=-180, le=180)
    mode: str = Field(
        default="drive",
        description="Phương thức di chuyển: drive, walk, bike (hoặc driving, walking, bicycling)"
    )

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v):
        """
        Validate và map mode về format Geoapify.
        """
        mode_mapping = {
            "driving": "drive",
            "walking": "walk",
            "bicycling": "bike",
            "transit": "drive",
            "drive": "drive",
            "walk": "walk",
            "bike": "bike"
        }

        v_lower = v.lower()
        if v_lower not in mode_mapping:
            allowed = list(mode_mapping.keys())
            raise ValueError(f"mode phải là một trong: {', '.join(allowed)}")
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


class LocationResponse(BaseModel):
    latitude: float
    longitude: float
    city: Optional[str] = None
    country: Optional[str] = None
    accuracy: str
    source: str


class PlaceResponse(BaseModel):
    place_id: str
    name: str
    category: str
    latitude: float
    longitude: float
    address: str
    distance: float
    phone: Optional[str] = None
    opening_hours: Optional[str] = None
    rating: Optional[float] = None
    website: Optional[str] = None
    marker_icon_url: str


class RouteStep(BaseModel):
    instruction: str
    distance: float
    duration: float


class RouteResponse(BaseModel):
    distance: float
    duration: float
    distance_km: float
    duration_minutes: float
    mode: str
    summary: str
    geometry: List[List[float]]
    steps: List[RouteStep]


class GeocodeResponse(BaseModel):
    latitude: float
    longitude: float
    formatted_address: str
    place_id: str
    city: Optional[str] = None
    country: Optional[str] = None


class ReverseGeocodeResponse(BaseModel):
    formatted_address: str
    street: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postcode: Optional[str] = None
