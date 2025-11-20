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

// Tọa độ mặc định (TP.HCM) nếu không lấy được vị trí
const DEFAULT_LOCATION = {
  lat: 10.7769,
  lon: 106.7009
};

// Component để cập nhật center của bản đồ khi location thay đổi
function MapUpdater({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, 14);
  }, [center, map]);
  return null;
}

const NearbyMap = () => {
  const [location, setLocation] = useState<{ lat: number; lon: number } | null>(
    null
  );
  const [places, setPlaces] = useState<Place[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isUsingDefault, setIsUsingDefault] = useState(false);
  const [searchAddress, setSearchAddress] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const getLocation = () => {
    setError(null);
    setIsUsingDefault(false);

    if (!navigator.geolocation) {
      useDefaultLocation("Trình duyệt không hỗ trợ định vị.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        });
        setIsUsingDefault(false); // Đã lấy được vị trí thật
      },
      (err) => {
        console.error("Error getting location:", err);
        
        // CHỈ hiển thị warning khi user TỪ CHỐI quyền
        if (err.code === err.PERMISSION_DENIED) {
          useDefaultLocation("Bạn đã từ chối quyền truy cập vị trí. Đang hiển thị vị trí mặc định.");
        } else {
          // Với các lỗi khác (POSITION_UNAVAILABLE, TIMEOUT), vẫn dùng default NHƯNG KHÔNG warning
          console.log("Using default location silently due to:", err.message);
          setLocation(DEFAULT_LOCATION);
          setIsUsingDefault(false); // Không hiển thị warning
        }
      },
      { 
        timeout: 10000, 
        enableHighAccuracy: false, 
        maximumAge: 60000 
      }
    );
  };

  const useDefaultLocation = (msg: string) => {
    console.log("Using default location:", msg);
    setLocation(DEFAULT_LOCATION);
    setIsUsingDefault(true);
    setError(msg);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchAddress.trim()) return;

    setIsSearching(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/map/geocode?address=${encodeURIComponent(searchAddress)}`
      );
      
      if (!response.ok) throw new Error("Failed to geocode address");
      
      const data = await response.json();
      
      if (data.results && data.results.length > 0) {
        const result = data.results[0];
        setLocation({
          lat: result.lat,
          lon: result.lon
        });
        setIsUsingDefault(false);
      } else {
        setError("Không tìm thấy địa chỉ này. Vui lòng thử lại.");
      }
    } catch (err) {
      console.error("Geocoding error:", err);
      setError("Lỗi khi tìm kiếm địa chỉ. Vui lòng thử lại.");
    } finally {
      setIsSearching(false);
    }
  };

  // 1. Lấy vị trí hiện tại khi component mount
  useEffect(() => {
    getLocation();
  }, []);

  // 2. Gọi API Backend khi có vị trí
  useEffect(() => {
    if (location) {
      fetch(
        `http://localhost:8000/api/v1/map/nearby?lat=${location.lat}&lon=${location.lon}&type=all`
      )
        .then((res) => {
          if (!res.ok) throw new Error("Failed to fetch places");
          return res.json();
        })
        .then((data) => setPlaces(data.places))
        .catch((err) => {
          console.error(err);
        });
    }
  }, [location]);

  if (!location) {
    return (
      <div
        style={{
          height: "500px",
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#f0f0f0",
          color: "#555",
        }}
      >
        <p>📍 Đang lấy vị trí...</p>
      </div>
    );
  }

  return (
    <div style={{ height: "500px", width: "100%", position: "relative" }}>
      {/* Search Box */}
      <form 
        onSubmit={handleSearch}
        style={{
          position: "absolute",
          top: "10px",
          left: "50%",
          transform: "translateX(-50%)",
          zIndex: 1000,
          display: "flex",
          gap: "8px",
          backgroundColor: "white",
          padding: "8px",
          borderRadius: "8px",
          boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
          width: "90%",
          maxWidth: "500px"
        }}
      >
        <input 
          type="text"
          value={searchAddress}
          onChange={(e) => setSearchAddress(e.target.value)}
          placeholder="Nhập địa chỉ (VD: Quận 1, TP.HCM)..."
          style={{
            flex: 1,
            padding: "8px 12px",
            border: "1px solid #ddd",
            borderRadius: "4px",
            fontSize: "0.9rem",
            outline: "none"
          }}
        />
        <button 
          type="submit"
          disabled={isSearching}
          style={{
            padding: "8px 16px",
            backgroundColor: "#009688",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: isSearching ? "wait" : "pointer",
            fontWeight: "600",
            fontSize: "0.9rem",
            opacity: isSearching ? 0.7 : 1
          }}
        >
          {isSearching ? "Đang tìm..." : "Tìm kiếm"}
        </button>
      </form>

      {/* Thông báo warning CHỈ KHI TỪ CHỐI quyền hoặc lỗi tìm kiếm */}
      {(isUsingDefault || error) && (
        <div style={{
          position: "absolute",
          top: "65px",
          left: "50%",
          transform: "translateX(-50%)",
          zIndex: 1000,
          backgroundColor: isUsingDefault ? "rgba(255, 193, 7, 0.9)" : "rgba(244, 67, 54, 0.9)",
          color: "white",
          padding: "8px 16px",
          borderRadius: "20px",
          fontSize: "0.85rem",
          fontWeight: "500",
          boxShadow: "0 2px 5px rgba(0,0,0,0.2)",
          maxWidth: "90%",
          textAlign: "center",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          flexDirection: "column"
        }}>
          <div>
            {isUsingDefault ? "⚠️ " : "❌ "} {error || "Đang hiển thị khu vực mặc định"}
          </div>
          {isUsingDefault && (
            <button 
              onClick={getLocation}
              style={{
                padding: "6px 12px",
                backgroundColor: "white",
                color: "#f57c00",
                border: "none",
                borderRadius: "12px",
                fontWeight: "600",
                fontSize: "0.8rem",
                cursor: "pointer"
              }}
            >
              🔄 Thử lại
            </button>
          )}
        </div>
      )}

      <MapContainer
        center={[location.lat, location.lon]}
        zoom={14}
        style={{ height: "100%", width: "100%" }}
      >
        <MapUpdater center={[location.lat, location.lon]} />
        <TileLayer
          url="https://maps.geoapify.com/v1/tile/carto/{z}/{x}/{y}.png?&apiKey=367fa9b8d99445f5bf95345289a7c39c"
          attribution='Powered by <a href="https://www.geoapify.com/" target="_blank">Geoapify</a> | © OpenStreetMap <a href="https://www.openstreetmap.org/copyright" target="_blank">contributors</a>'
        />

        {/* Marker của User */}
        <Marker position={[location.lat, location.lon]}>
          <Popup>Vị trí của bạn</Popup>
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