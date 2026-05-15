import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings



class MapService:
    def __init__(self):
        self.api_key = settings.GEOAPIFY_API_KEY
        self.base_url = "https://api.geoapify.com"
        self.timeout = 10.0

    async def get_ip_location(self, client_ip: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/ipinfo"
        params: Dict[str, Any] = {"apiKey": self.api_key}
        if client_ip:
            params["ip"] = client_ip

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        result = {
            "latitude": data["location"]["latitude"],
            "longitude": data["location"]["longitude"],
            "city": data.get("city", {}).get("name", "Unknown"),
            "country": data.get("country", {}).get("name", "Unknown"),
            "accuracy": "ip_based",
            "source": "ip",
            "raw_data": data
        }

        return result

    async def find_nearby_places(
        self,
        latitude: float,
        longitude: float,
        category: str = "healthcare",
        radius: int = 5000,
        limit: int = 20
    ) -> List[Dict[str, Any]]:

        url = f"{self.base_url}/v2/places"

        filter_area = f"circle:{longitude},{latitude},{radius}"

        # Map category to Geoapify format
        geoapify_category = self._map_category_to_geoapify(category)

        params = {
            "categories": geoapify_category,
            "filter": filter_area,
            "limit": limit,
            "apiKey": self.api_key
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        places = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            coords = feature.get("geometry", {}).get("coordinates", [0, 0])

            place = {
                "place_id": props.get("place_id", ""),
                "name": props.get("name", "Unnamed"),
                "category": props.get("categories", [None])[0] if props.get("categories") else category,
                "longitude": coords[0],
                "latitude": coords[1],
                "address": self._format_address(props),
                "distance": props.get("distance") if props.get("distance") is not None else self._calculate_haversine_distance(latitude, longitude, coords[1], coords[0]),
                "phone": props.get("datasource", {}).get("raw", {}).get("phone"),
                "opening_hours": props.get("opening_hours"),
                "rating": props.get("datasource", {}).get("raw", {}).get("rating"),
                "website": props.get("datasource", {}).get("raw", {}).get("website"),
            }
            places.append(place)

        return places

    async def calculate_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        mode: str = "drive"  # drive, walk, bike
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/routing"

        waypoints = f"{start_lat},{start_lon}|{end_lat},{end_lon}"

        geoapify_mode = "bicycle" if mode == "bike" else mode

        params = {
            "waypoints": waypoints,
            "mode": geoapify_mode,
            "apiKey": self.api_key
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # Extract thông tin route
        features = data.get("features", [])
        if not features:
            return {
                "distance": 0,
                "duration": 0,
                "geometry": [],
                "steps": [],
                "mode": mode
            }

        feature = features[0]
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        coordinates = geometry.get("coordinates", [])

        geometry_points = []
        if coordinates:
            if isinstance(coordinates[0][0], list):
                coords_list = coordinates[0]
            else:
                coords_list = coordinates

            geometry_points = [[coord[1], coord[0]] for coord in coords_list]

        steps = []
        for leg in props.get("legs", []):
            for step in leg.get("steps", []):
                steps.append({
                    "instruction": step.get("instruction", {}).get("text", ""),
                    "distance": step.get("distance", 0),
                    "duration": step.get("time", 0)
                })

        result = {
            "distance": props.get("distance", 0),  # mét
            "duration": props.get("time", 0),  # giây
            "geometry": geometry_points,
            "steps": steps,
            "mode": mode
        }

        return result

    async def geocode_address(
        self,
        address: str,
        bias_lat: Optional[float] = None,
        bias_lon: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/v1/geocode/search"

        params: Dict[str, Any] = {
            "apiKey": self.api_key,
            "text": address,
            "limit": 1,
            "filter": "countrycode:vn",
            "lang": "vi",
        }
        if bias_lat is not None and bias_lon is not None:
            params["bias"] = f"proximity:{bias_lon},{bias_lat}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        features = data.get("features", [])
        if not features:
            # Retry without country filter as fallback
            params.pop("filter", None)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            features = data.get("features", [])
            if not features:
                return None

        feature = features[0]
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [0, 0])

        result = {
            "latitude": coords[1],
            "longitude": coords[0],
            "formatted_address": props.get("formatted", address),
            "place_id": props.get("place_id", ""),
            "city": props.get("city", ""),
            "country": props.get("country", "")
        }

        return result

    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/v1/geocode/reverse"

        params = {
            "lat": latitude,
            "lon": longitude,
            "apiKey": self.api_key
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        features = data.get("features", [])
        if not features:
            return None

        props = features[0].get("properties", {})

        result = {
            "formatted_address": props.get("formatted", "Unknown address"),
            "street": props.get("street", ""),
            "city": props.get("city", ""),
            "country": props.get("country", ""),
            "postcode": props.get("postcode", "")
        }

        return result

    def get_marker_icon_url(
        self,
        icon: str = "hospital",
        color: str = "red",
        size: str = "medium",
        icon_type: str = "awesome"
    ) -> str:
        size_map = {
            "small": "small",
            "medium": "medium",
            "large": "large"
        }

        url = (
            f"{self.base_url}/v1/icon?"
            f"type={icon_type}&"
            f"color={color}&"
            f"size={size_map.get(size, 'medium')}&"
            f"icon={icon}&"
            f"apiKey={self.api_key}"
        )

        return url

    def _map_category_to_geoapify(self, category: str) -> str:
        """
        Map user-friendly category names to Geoapify's category format.
        Accepts both short aliases ("pharmacy") and full geoapify ids
        ("healthcare.pharmacy"). Pharmacy returns multiple variants because
        Geoapify indexes pharmacies under both healthcare and commercial trees.
        """
        category_mapping = {
            "hospital": "healthcare.hospital",
            "clinic": "healthcare.clinic_or_praxis,healthcare.clinic,healthcare.doctors",
            "pharmacy": "healthcare.pharmacy,commercial.health_and_beauty.pharmacy",
            "dentist": "healthcare.dentist",
            "all": "healthcare",
            "healthcare": "healthcare",
            "healthcare.hospital": "healthcare.hospital",
            "healthcare.clinic": "healthcare.clinic_or_praxis,healthcare.clinic,healthcare.doctors",
            "healthcare.clinic_or_praxis": "healthcare.clinic_or_praxis,healthcare.clinic,healthcare.doctors",
            "healthcare.pharmacy": "healthcare.pharmacy,commercial.health_and_beauty.pharmacy",
            "healthcare.dentist": "healthcare.dentist",
        }

        return category_mapping.get(category.lower(), category)

    def _format_address(self, properties: Dict[str, Any]) -> str:
        if "formatted" in properties:
            return properties["formatted"]
        parts = []

        if "housenumber" in properties:
            parts.append(properties["housenumber"])
        if "street" in properties:
            parts.append(properties["street"])
        if "city" in properties:
            parts.append(properties["city"])
        if "country" in properties:
            parts.append(properties["country"])

        return ", ".join(parts) if parts else "Unknown address"

    def _calculate_haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> int:
        import math
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return int(R * c)
