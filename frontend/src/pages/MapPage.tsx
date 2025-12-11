import { useState, useEffect, useCallback } from "react";
import { useOutletContext } from "react-router-dom";
import { useTranslation } from "react-i18next";
import i18n from "../i18n";
import SearchBar from "../components/map/SearchBar";
import RadiusSlider from "../components/map/RadiusSlider";
import FilterChips from "../components/map/FilterChips";
import FacilityCard, { type Facility } from "../components/map/FacilityCard";
import MapView from "../components/map/MapView";
import DirectionsPanel from "../components/map/DirectionsPanel";
import mapService, { type RouteResponse } from "../services/mapService";
import {
  FaArrowLeft,
  FaBars,
  FaList,
  FaMap,
  FaLocationArrow,
} from "react-icons/fa";
import type { MainLayoutContextType } from "../components/layout/MainLayout";
import "./MapPage.css";

const MapPage = () => {
  const { t } = useTranslation();
  const { setMenuOpen } = useOutletContext<MainLayoutContextType>();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("all");
  const [radius, setRadius] = useState(5); // Default 5km
  const [showFilters, setShowFilters] = useState(false);
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [userLocation, setUserLocation] = useState<
    { lat: number; lng: number } | undefined
  >(undefined);
  const [loading, setLoading] = useState(false);
  const [locationLoading, setLocationLoading] = useState(true);
  const [locationError, setLocationError] = useState<string | null>(null);

  // Mobile view toggle state
  const [mobileView, setMobileView] = useState<"list" | "map">("list");

  // Directions state
  const [directionsMode, setDirectionsMode] = useState(false);
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(
    null
  );
  const [routeData, setRouteData] = useState<RouteResponse | null>(null);
  const [travelMode, setTravelMode] = useState<"drive" | "walk" | "bike">(
    "drive"
  );

  // Get user location on mount
  const requestUserLocation = useCallback(() => {
    setLocationLoading(true);
    setLocationError(null);

    // Default location: Da Nang, Vietnam (only used as last resort)
    const fallbackLocation = { lat: 16.0474546, lng: 108.1992956 };

    if (!navigator.geolocation) {
      setLocationError(t("map.geolocation_not_supported"));
      setUserLocation(fallbackLocation);
      setLocationLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
        setLocationError(null);
        setLocationLoading(false);
      },
      (error) => {
        let errorMessage = t("map.location_error");
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = t("map.location_permission_denied");
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = t("map.location_unavailable");
            break;
          case error.TIMEOUT:
            errorMessage = t("map.location_timeout");
            break;
        }
        console.log("Geolocation error:", errorMessage);
        setLocationError(errorMessage);
        setUserLocation(fallbackLocation);
        setLocationLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 300000, // 5 minutes cache
      }
    );
  }, [t]);

  useEffect(() => {
    requestUserLocation();
  }, [requestUserLocation]);

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

  const fetchRoute = async (
    start: { lat: number; lng: number },
    end: { lat: number; lng: number },
    mode: "drive" | "walk" | "bike"
  ) => {
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
      alert(t("map.alert_route_error"));
    }
  };

  const handleDirections = (facility: Facility) => {
    if (!userLocation) {
      alert(t("map.alert_location_required"));
      return;
    }
    setSelectedFacility(facility);
    setDirectionsMode(true);
    fetchRoute(
      userLocation,
      { lat: facility.lat, lng: facility.lng },
      travelMode
    );
  };

  const handleModeChange = (mode: "drive" | "walk" | "bike") => {
    setTravelMode(mode);
    if (userLocation && selectedFacility) {
      fetchRoute(
        userLocation,
        { lat: selectedFacility.lat, lng: selectedFacility.lng },
        mode
      );
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
        text: t("map.share_text", {
          name: facility.name,
          address: facility.address,
        }),
        url: window.location.href,
      });
    } else {
      // Fallback
      navigator.clipboard.writeText(`${facility.name}\n${facility.address}`);
      alert(t("map.alert_copied"));
    }
  };

  return (
    <div className="map-page">
      <title>{t("title.map_page")}</title>
      <div
        className={`map-sidebar ${
          mobileView === "list" ? "mobile-show" : "mobile-hide"
        }`}
      >
        {directionsMode && selectedFacility && routeData ? (
          <DirectionsPanel
            startAddress={t("map.your_location")}
            endAddress={selectedFacility.name}
            duration={`${routeData.duration_minutes} ${
              i18n.language === "en" ? "min" : "phút"
            }`}
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
                <h1 className="map-title">{t("map.title")}</h1>
              </div>
              <p className="map-subtitle">{t("map.subtitle")}</p>

              {/* Location status */}
              {locationError && (
                <div className="location-status location-error">
                  <span>{locationError}</span>
                  <button
                    className="retry-location-btn"
                    onClick={requestUserLocation}
                    disabled={locationLoading}
                  >
                    <FaLocationArrow />
                    {locationLoading
                      ? t("map.getting_location")
                      : t("map.retry_location")}
                  </button>
                </div>
              )}

              {/* Mobile View Toggle */}
              <div className="mobile-view-toggle">
                <button
                  className={`view-toggle-btn ${
                    mobileView === "list" ? "active" : ""
                  }`}
                  onClick={() => setMobileView("list")}
                  aria-label="List view"
                >
                  <FaList />
                  <span>{t("map.list_view")}</span>
                </button>
                <button
                  className={`view-toggle-btn ${
                    mobileView === "map" ? "active" : ""
                  }`}
                  onClick={() => setMobileView("map")}
                  aria-label="Map view"
                >
                  <FaMap />
                  <span>{t("map.map_view")}</span>
                </button>
              </div>
            </div>

            <div className="map-sidebar-controls">
              <RadiusSlider value={radius} onChange={setRadius} />
            </div>

            <div className="map-results-header">
              <h2 className="font-semibold">
                {t("map.results")}
                <span className="results-count">
                  {filteredFacilities.length} {t("map.facilities")}
                </span>
              </h2>
            </div>

            <div className="map-results-list">
              {loading ? (
                <div className="no-results">{t("map.loading")}</div>
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
                  <p>{t("map.no_results")}</p>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      <div
        className={`map-view-wrapper ${
          mobileView === "map" ? "mobile-show" : "mobile-hide"
        }`}
      >
        {/* Floating back button for mobile map view */}
        {mobileView === "map" && (
          <button
            className="map-back-btn"
            onClick={() => {
              if (directionsMode) {
                // If in directions mode, first exit directions
                handleBackFromDirections();
              }
              setMobileView("list");
            }}
            aria-label={t("map.back_to_list")}
          >
            <FaArrowLeft />
            <span>{t("map.back_to_list")}</span>
          </button>
        )}
        {!directionsMode && (
          <div className="map-overlay-container">
            <div className="map-overlay-search">
              <SearchBar
                value={searchQuery}
                onChange={setSearchQuery}
                onFilterClick={() => setShowFilters(!showFilters)}
                onSearch={() => {}}
              />
            </div>
            <div className="map-overlay-filters">
              <FilterChips
                selected={selectedFilter}
                onChange={setSelectedFilter}
              />
            </div>
          </div>
        )}
        <MapView
          userLocation={userLocation}
          facilities={
            directionsMode && selectedFacility
              ? [selectedFacility]
              : filteredFacilities
          }
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
