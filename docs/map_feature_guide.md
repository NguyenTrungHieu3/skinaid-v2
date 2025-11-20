# Hướng Dẫn Triển Khai Tính Năng Bản Đồ (Map Feature) - A đến Z

Tài liệu này hướng dẫn chi tiết cách tích hợp tính năng tìm kiếm Bệnh viện/Nhà thuốc gần nhất sử dụng **Leaflet** (Frontend) và **Geoapify** (Backend Data).

## 1. Chuẩn Bị (Setup)

### 1.1. Đăng ký Geoapify API Key

1.  Truy cập [Geoapify](https://www.geoapify.com/) và đăng ký tài khoản (Free Tier).
2.  Tạo một Project mới.
3.  Copy **API Key**.

### 1.2. Cấu hình Backend

Thêm API Key vào file `.env` trong thư mục `backend/`:

```env
GEOAPIFY_API_KEY=your_api_key_here
```

### 1.3. Cài đặt thư viện Frontend

Mở terminal tại thư mục `frontend/` và chạy lệnh:

```bash
npm install leaflet react-leaflet
npm install -D @types/leaflet
```

---

## 2. Triển Khai Backend (FastAPI)

Chúng ta sẽ tạo một module mới là `map` để xử lý các logic liên quan đến bản đồ.

### 2.1. Cấu trúc thư mục

Tạo thư mục: `backend/app/modules/map/`
Các file cần tạo:

- `__init__.py`
- `schemas.py`: Định nghĩa dữ liệu đầu ra.
- `services.py`: Gọi API Geoapify.
- `controller.py`: Xử lý logic nghiệp vụ.
- `router.py`: Định nghĩa API endpoint.

### 2.2. Code chi tiết

**`backend/app/modules/map/schemas.py`**

```python
from pydantic import BaseModel
from typing import List, Optional

class Location(BaseModel):
    lat: float
    lon: float

class Place(BaseModel):
    name: str
    address: str
    location: Location
    distance: Optional[float] = None
    place_id: str

class NearbyPlacesResponse(BaseModel):
    places: List[Place]
```

**`backend/app/modules/map/services.py`**

```python
import httpx
import os
from typing import List, Dict, Any

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
GEOAPIFY_URL = "https://api.geoapify.com/v2/places"

async def get_nearby_places(lat: float, lon: float, categories: str = "healthcare.hospital,healthcare.pharmacy", limit: int = 20) -> List[Dict[str, Any]]:
    if not GEOAPIFY_API_KEY:
        raise Exception("GEOAPIFY_API_KEY not found in environment variables")

    params = {
        "categories": categories,
        "filter": f"circle:{lon},{lat},5000", # Bán kính 5km
        "bias": f"proximity:{lon},{lat}",
        "limit": limit,
        "apiKey": GEOAPIFY_API_KEY
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(GEOAPIFY_URL, params=params)
        response.raise_for_status()
        data = response.json()

        results = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            results.append({
                "name": props.get("name", "Unknown"),
                "address": props.get("formatted", ""),
                "location": {
                    "lat": geometry.get("coordinates", [0, 0])[1],
                    "lon": geometry.get("coordinates", [0, 0])[0]
                },
                "distance": props.get("distance"),
                "place_id": props.get("place_id")
            })
        return results
```

**`backend/app/modules/map/router.py`**

```python
from fastapi import APIRouter, HTTPException, Query
from app.modules.map import services
from app.modules.map.schemas import NearbyPlacesResponse

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
```

**Đăng ký Router**: Đừng quên thêm `router` vào `main.py` hoặc `app_router.py`.

---

## 3. Triển Khai Frontend (React + Leaflet)

### 3.1. Tạo Component Map

Tạo file `frontend/src/components/Map/NearbyMap.tsx`.

```tsx
import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix icon lỗi mặc định của Leaflet trong React
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

interface Place {
  name: string;
  address: string;
  location: { lat: number; lon: number };
  distance?: number;
}

const NearbyMap = () => {
  const [location, setLocation] = useState<{ lat: number; lon: number } | null>(
    null
  );
  const [places, setPlaces] = useState<Place[]>([]);

  // 1. Lấy vị trí hiện tại
  useEffect(() => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        });
      },
      (error) => console.error("Error getting location:", error)
    );
  }, []);

  // 2. Gọi API Backend khi có vị trí
  useEffect(() => {
    if (location) {
      fetch(
        `http://localhost:8000/api/v1/map/nearby?lat=${location.lat}&lon=${location.lon}&type=all`
      )
        .then((res) => res.json())
        .then((data) => setPlaces(data.places))
        .catch((err) => console.error(err));
    }
  }, [location]);

  if (!location) return <div>Đang lấy vị trí của bạn...</div>;

  return (
    <div style={{ height: "500px", width: "100%" }}>
      <MapContainer
        center={[location.lat, location.lon]}
        zoom={14}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />

        {/* Marker của User */}
        <Marker position={[location.lat, location.lon]}>
          <Popup>Bạn đang ở đây</Popup>
        </Marker>

        {/* Marker các địa điểm tìm được */}
        {places.map((place, idx) => (
          <Marker key={idx} position={[place.location.lat, place.location.lon]}>
            <Popup>
              <strong>{place.name}</strong>
              <br />
              {place.address}
              <br />
              Cách đây: {place.distance}m
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
};

export default NearbyMap;
```

### 3.2. Sử dụng Component

Import `NearbyMap` vào trang bạn muốn hiển thị (ví dụ `HomePage.tsx`).

```tsx
import NearbyMap from "../components/Map/NearbyMap";

const HomePage = () => {
  return (
    <div>
      <h1>Tìm kiếm Bệnh viện & Nhà thuốc</h1>
      <NearbyMap />
    </div>
  );
};
```

---

## 4. Chạy và Kiểm Thử (Run & Test)

### 4.1. Chạy Backend

```bash
cd backend
# Kích hoạt venv nếu cần
uvicorn app.main:app --reload
```

### 4.2. Chạy Frontend

```bash
cd frontend
npm run dev
```

### 4.3. Kiểm thử

1.  Mở trình duyệt (Chrome/Edge).
2.  Truy cập trang có bản đồ.
3.  **Quan trọng**: Trình duyệt sẽ hỏi quyền truy cập vị trí -> Chọn **Allow**.
4.  Kiểm tra xem bản đồ có hiện ra không, marker "Bạn đang ở đây" có đúng vị trí không.
5.  Kiểm tra xem các marker bệnh viện/nhà thuốc xung quanh có hiện ra không.

## 5. Lưu ý quan trọng

- **Bảo mật**: Không bao giờ commit `.env` chứa API Key lên Git.
- **CORS**: Đảm bảo Backend đã cấu hình CORS cho phép Frontend gọi API.
- **Production**: Khi deploy, hãy thay đổi URL API trong Frontend từ `localhost` sang domain thật.
