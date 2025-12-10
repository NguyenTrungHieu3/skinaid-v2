import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { FaTimes, FaMapMarkerAlt, FaSpinner } from "react-icons/fa";
import MapView from "../map/MapView";
import DirectionsPanel from "../map/DirectionsPanel";
import FacilityCard, { type Facility } from "../map/FacilityCard";
import mapService, { type RouteResponse } from "../../services/mapService";
import i18n from "../../i18n";
import styles from "./MapModal.module.css";

interface MapModalProps {
  isOpen: boolean;
  onClose: () => void;
}

/**
 * Modal component displaying a map with nearby medical facilities
 * and directions. Used when wound severity is moderate or severe.
 */
const MapModal = ({ isOpen, onClose }: MapModalProps) => {
  const { t } = useTranslation();

  // Location state
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [loadingLocation, setLoadingLocation] = useState(true);

  // Facilities state
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loadingFacilities, setLoadingFacilities] = useState(false);

  // Directions state
  const [directionsMode, setDirectionsMode] = useState(false);
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null);
  const [routeData, setRouteData] = useState<RouteResponse | null>(null);
  const [travelMode, setTravelMode] = useState<"drive" | "walk" | "bike">("drive");

  // Get user location on modal open
  useEffect(() => {
    if (!isOpen) return;

    // Default location: Da Nang, Vietnam
    const DEFAULT_LOCATION = { lat: 16.0474546, lng: 108.1992956 };

    const fetchLocation = async () => {
      setLoadingLocation(true);
      setLocationError(null);

      try {
        // Try browser geolocation first
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            (position) => {
              setUserLocation({
                lat: position.coords.latitude,
                lng: position.coords.longitude,
              });
              setLoadingLocation(false);
            },
            () => {
              // Fallback to default location (Da Nang, Vietnam)
              console.log("Geolocation denied, using default location");
              setUserLocation(DEFAULT_LOCATION);
              setLoadingLocation(false);
            },
            { 
              enableHighAccuracy: true,
              timeout: 10000,
              maximumAge: 300000
            }
          );
        } else {
          // No geolocation support, use default
          setUserLocation(DEFAULT_LOCATION);
          setLoadingLocation(false);
        }
      } catch {
        setLocationError(t("map_modal.location_error"));
        setUserLocation(DEFAULT_LOCATION);
        setLoadingLocation(false);
      }
    };

    fetchLocation();
  }, [isOpen, t]);

  // Fetch nearby medical facilities when location is available
  useEffect(() => {
    if (!userLocation || !isOpen) return;

    const fetchFacilities = async () => {
      setLoadingFacilities(true);
      try {
        // Search for hospitals within 10km
        const response = await mapService.findNearbyPlaces({
          latitude: userLocation.lat,
          longitude: userLocation.lng,
          radius: 10000, // 10km
          category: "hospital",
          limit: 10,
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
        setLoadingFacilities(false);
      }
    };

    fetchFacilities();
  }, [userLocation, isOpen]);

  // Fetch route
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
        text: t("map.share_text", { name: facility.name, address: facility.address }),
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(`${facility.name}\n${facility.address}`);
      alert(t("map.alert_copied"));
    }
  };

  // Close modal on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerContent}>
            <FaMapMarkerAlt className={styles.headerIcon} />
            <div>
              <h2 className={styles.title}>{t("map_modal.title")}</h2>
              <p className={styles.subtitle}>{t("map_modal.subtitle")}</p>
            </div>
          </div>
          <button className={styles.closeButton} onClick={onClose} aria-label="Close">
            <FaTimes />
          </button>
        </div>

        {/* Content */}
        <div className={styles.content}>
          {/* Sidebar */}
          <div className={styles.sidebar}>
            {loadingLocation ? (
              <div className={styles.loading}>
                <FaSpinner className={styles.spinner} />
                <p>{t("map_modal.loading_location")}</p>
              </div>
            ) : locationError ? (
              <div className={styles.error}>
                <p>{locationError}</p>
              </div>
            ) : directionsMode && selectedFacility && routeData ? (
              <DirectionsPanel
                startAddress={t("map.your_location")}
                endAddress={selectedFacility.name}
                duration={`${routeData.duration_minutes} ${i18n.language === "en" ? "min" : "phút"}`}
                distance={`${routeData.distance_km} km`}
                mode={travelMode}
                steps={routeData.steps}
                onBack={handleBackFromDirections}
                onModeChange={handleModeChange}
              />
            ) : (
              <>
                <div className={styles.resultsHeader}>
                  <h3>
                    {t("map_modal.nearby_facilities")}
                    <span className={styles.count}>
                      {facilities.length} {t("map.facilities")}
                    </span>
                  </h3>
                </div>
                <div className={styles.facilityList}>
                  {loadingFacilities ? (
                    <div className={styles.loading}>
                      <FaSpinner className={styles.spinner} />
                      <p>{t("map.loading")}</p>
                    </div>
                  ) : facilities.length > 0 ? (
                    facilities.map((facility) => (
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
                    <div className={styles.noResults}>
                      <p>{t("map.no_results")}</p>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Map */}
          <div className={styles.mapContainer}>
            <MapView
              userLocation={userLocation || undefined}
              facilities={directionsMode && selectedFacility ? [selectedFacility] : facilities}
              routeGeometry={routeData?.geometry as [number, number][] | undefined}
              onDirections={handleDirections}
              onCall={handleCall}
              onWebsite={handleWebsite}
              onShare={handleShare}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapModal;
