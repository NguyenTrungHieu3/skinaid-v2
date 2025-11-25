import { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import SearchBar from "../components/map/SearchBar";
import RadiusSlider from "../components/map/RadiusSlider";
import FilterChips from "../components/map/FilterChips";
import FacilityCard, { type Facility } from "../components/map/FacilityCard";
import MapView from "../components/map/MapView";
import DirectionsPanel from "../components/map/DirectionsPanel";
import mapService, { type RouteResponse } from "../services/mapService";
import { FaBars } from "react-icons/fa";
import type { MainLayoutContextType } from "../components/layout/MainLayout";
import "./MapPage.css";

const MapPage = () => {
    const { setMenuOpen } = useOutletContext<MainLayoutContextType>();
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedFilter, setSelectedFilter] = useState("all");
    const [radius, setRadius] = useState(5); // Default 5km
    const [showFilters, setShowFilters] = useState(false);
    const [facilities, setFacilities] = useState<Facility[]>([]);
    const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | undefined>(undefined);
    const [loading, setLoading] = useState(false);

    // Directions state
    const [directionsMode, setDirectionsMode] = useState(false);
    const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null);
    const [routeData, setRouteData] = useState<RouteResponse | null>(null);
    const [travelMode, setTravelMode] = useState<"drive" | "walk" | "bike">("drive");

    // Get user location on mount
    useEffect(() => {
        const fetchLocation = async () => {
            try {
                // Try to get from browser geolocation first
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            setUserLocation({
                                lat: position.coords.latitude,
                                lng: position.coords.longitude,
                            });
                        },
                        async () => {
                            // Fallback to IP location
                            try {
                                const loc = await mapService.getIpLocation();
                                setUserLocation({ lat: loc.latitude, lng: loc.longitude });
                            } catch (error) {
                                console.error("Error getting IP location:", error);
                            }
                        }
                    );
                } else {
                    // Fallback to IP location
                    const loc = await mapService.getIpLocation();
                    setUserLocation({ lat: loc.latitude, lng: loc.longitude });
                }
            } catch (error) {
                console.error("Error getting location:", error);
            }
        };

        fetchLocation();
    }, []);

    // Fetch facilities when location or filters change
    useEffect(() => {
        if (!userLocation || directionsMode) return;

        const fetchFacilities = async () => {
            setLoading(true);
            try {
                const category = selectedFilter === "all" ? undefined : selectedFilter;

                const response = await mapService.findNearbyPlaces({
                    latitude: userLocation.lat,
                    longitude: userLocation.lng,
                    radius: radius * 1000, // convert to meters
                    category: category,
                    limit: 50,
                });

                const mappedFacilities: Facility[] = response.map((place) => ({
                    id: place.place_id,
                    name: place.name,
                    type: place.category,
                    address: place.address,
                    phone: place.phone,
                    hours: place.opening_hours,
                    distance: place.distance,
                    website: place.website,
                    lat: place.latitude,
                    lng: place.longitude,
                }));

                setFacilities(mappedFacilities);
            } catch (error) {
                console.error("Error fetching facilities:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchFacilities();
    }, [userLocation, radius, selectedFilter, directionsMode]);

    // Filter locally by search query
    const filteredFacilities = facilities.filter((facility) => {
        const matchesSearch =
            facility.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            facility.address.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesSearch;
    });

    const fetchRoute = async (start: { lat: number; lng: number }, end: { lat: number; lng: number }, mode: "drive" | "walk" | "bike") => {
        try {
            const route = await mapService.calculateRoute({
                start_latitude: start.lat,
                start_longitude: start.lng,
                end_latitude: end.lat,
                end_longitude: end.lng,
                mode: mode,
            });
            setRouteData(route);
        } catch (error) {
            console.error("Error fetching route:", error);
            alert("Không thể tìm thấy đường đi");
        }
    };

    const handleDirections = (facility: Facility) => {
        if (!userLocation) {
            alert("Vui lòng cho phép truy cập vị trí để sử dụng tính năng chỉ đường");
            return;
        }
        setSelectedFacility(facility);
        setDirectionsMode(true);
        fetchRoute(userLocation, { lat: facility.lat, lng: facility.lng }, travelMode);
    };

    const handleModeChange = (mode: "drive" | "walk" | "bike") => {
        setTravelMode(mode);
        if (userLocation && selectedFacility) {
            fetchRoute(userLocation, { lat: selectedFacility.lat, lng: selectedFacility.lng }, mode);
        }
    };

    const handleBackFromDirections = () => {
        setDirectionsMode(false);
        setRouteData(null);
        setSelectedFacility(null);
    };

    const handleCall = (phone: string) => {
        window.location.href = `tel:${phone}`;
    };

    const handleWebsite = (url: string) => {
        window.open(url, "_blank");
    };

    const handleShare = (facility: Facility) => {
        if (navigator.share) {
            navigator.share({
                title: facility.name,
                text: `Cơ sở y tế: ${facility.name}\n${facility.address}`,
                url: window.location.href,
            });
        } else {
            // Fallback
            navigator.clipboard.writeText(`${facility.name}\n${facility.address}`);
            alert("Đã sao chép thông tin vào clipboard");
        }
    };

    return (
        <div className="map-page">
            <div className="map-sidebar">
                {directionsMode && selectedFacility && routeData ? (
                    <DirectionsPanel
                        startAddress="Vị trí của bạn"
                        endAddress={selectedFacility.name}
                        duration={`${routeData.duration_minutes} phút`}
                        distance={`${routeData.distance_km} km`}
                        mode={travelMode}
                        steps={routeData.steps}
                        onBack={handleBackFromDirections}
                        onModeChange={handleModeChange}
                    />
                ) : (
                    <>
                        <div className="map-header">
                            <div className="map-header-top">
                                <button
                                    className="map-menu-btn"
                                    onClick={() => setMenuOpen(true)}
                                    aria-label="Open menu"
                                >
                                    <FaBars />
                                </button>
                                <h1 className="map-title">Nearby Medical Facility</h1>
                            </div>
                            <p className="map-subtitle">Tìm kiếm bệnh viện, phòng khám gần bạn</p>
                        </div>

                        <div className="map-sidebar-controls">
                            <RadiusSlider value={radius} onChange={setRadius} />
                        </div>

                        <div className="map-results-header">
                            <h2 className="font-semibold">
                                Kết quả
                                <span className="results-count">{filteredFacilities.length} cơ sở</span>
                            </h2>
                        </div>

                        <div className="map-results-list">
                            {loading ? (
                                <div className="no-results">Đang tải...</div>
                            ) : filteredFacilities.length > 0 ? (
                                filteredFacilities.map((facility) => (
                                    <FacilityCard
                                        key={facility.id}
                                        facility={facility}
                                        onDirections={handleDirections}
                                        onCall={handleCall}
                                        onWebsite={handleWebsite}
                                        onShare={handleShare}
                                    />
                                ))
                            ) : (
                                <div className="no-results">
                                    <p>Không tìm thấy cơ sở y tế phù hợp</p>
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>

            <div className="map-view-wrapper">
                {!directionsMode && (
                    <div className="map-overlay-container">
                        <div className="map-overlay-search">
                            <SearchBar
                                value={searchQuery}
                                onChange={setSearchQuery}
                                onFilterClick={() => setShowFilters(!showFilters)}
                                onSearch={() => { }}
                            />
                        </div>
                        <div className="map-overlay-filters">
                            <FilterChips selected={selectedFilter} onChange={setSelectedFilter} />
                        </div>
                    </div>
                )}
                <MapView
                    userLocation={userLocation}
                    facilities={directionsMode && selectedFacility ? [selectedFacility] : filteredFacilities}
                    routeGeometry={routeData?.geometry as [number, number][] | undefined}
                    onDirections={handleDirections}
                    onCall={handleCall}
                    onWebsite={handleWebsite}
                    onShare={handleShare}
                />
            </div>
        </div>
    );
};

export default MapPage;
