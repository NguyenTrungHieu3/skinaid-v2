import httpx
from typing import List, Dict, Any
from app.core.config import settings

GEOAPIFY_API_KEY = settings.GEOAPIFY_API_KEY
GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"
GEOAPIFY_GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"

async def get_nearby_places(
    lat: float, 
    lon: float, 
    categories: str = "healthcare.hospital,healthcare.pharmacy", 
    limit: int = 20
) -> List[Dict[str, Any]]:
    if not GEOAPIFY_API_KEY: 
        raise Exception("Không tìm thấy GEOAPIFY_API_KEY trong các biến môi trường")

    params = {
        "categories": categories, 
        "filter":  f"circle:{lon},{lat},5000",
        "bias": f"proximity:{lon},{lat}", 
        "limit": limit, 
        "apiKey": GEOAPIFY_API_KEY
    }

    async with httpx.AsyncClient() as client: 
        response = await client.get(GEOAPIFY_PLACES_URL, params=params)
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

async def geocode_address(address: str) -> List[Dict[str, Any]]:
    """
    Chuyển đổi địa chỉ text thành tọa độ (lat, lon)
    """
    if not GEOAPIFY_API_KEY:
        raise Exception("Không tìm thấy GEOAPIFY_API_KEY trong các biến môi trường")
    
    params = {
        "text": address,
        "format": "json",
        "apiKey": GEOAPIFY_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(GEOAPIFY_GEOCODE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for result in data.get("results", []):
            results.append({
                "lat": result.get("lat"),
                "lon": result.get("lon"),
                "formatted_address": result.get("formatted", "")
            })
        return results