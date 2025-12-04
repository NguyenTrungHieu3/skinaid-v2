import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap, Polyline } from "react-leaflet";
import { useTranslation } from "react-i18next";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { Phone, MapPin, Globe, Share2, Navigation } from "lucide-react";
import type { Facility } from "./FacilityCard";
import "./MapView.css";

// Custom Icon Generator
const createCustomIcon = (color: string) => {
    return L.divIcon({
        className: "custom-marker-icon",
        html: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${color}" width="48px" height="48px" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
      </svg>
    `,
        iconSize: [48, 48],
        iconAnchor: [24, 48],
        popupAnchor: [0, -48],
    });
};

const UserIcon = createCustomIcon("#3b82f6"); // Blue
const DestinationIcon = createCustomIcon("#ef4444"); // Red
const FacilityIcon = createCustomIcon("#009688"); // Teal

interface MapViewProps {
    userLocation?: { lat: number; lng: number };
    facilities: Facility[];
    routeGeometry?: Array<[number, number]>;
    onDirections?: (facility: Facility) => void;
    onCall?: (phone: string) => void;
    onWebsite?: (url: string) => void;
    onShare?: (facility: Facility) => void;
}

function ChangeView({ center, zoom }: { center: [number, number]; zoom: number }) {
    const map = useMap();
    useEffect(() => {
        map.setView(center, zoom);
    }, [center, zoom, map]);
    return null;
}

// Component to handle map resize when container visibility changes
function MapResizeHandler() {
    const map = useMap();
    
    useEffect(() => {
        // Initial invalidateSize after mount
        const timer = setTimeout(() => {
            map.invalidateSize();
        }, 100);

        // Also invalidateSize on window resize
        const handleResize = () => {
            map.invalidateSize();
        };

        window.addEventListener('resize', handleResize);
        
        // Use ResizeObserver to detect container size changes
        const container = map.getContainer();
        const resizeObserver = new ResizeObserver(() => {
            map.invalidateSize();
        });
        resizeObserver.observe(container);

        return () => {
            clearTimeout(timer);
            window.removeEventListener('resize', handleResize);
            resizeObserver.disconnect();
        };
    }, [map]);

    return null;
}

const MapView = ({
    userLocation,
    facilities,
    routeGeometry,
    onDirections,
    onCall,
    onWebsite,
    onShare
}: MapViewProps) => {
    const { t } = useTranslation();
    const defaultCenter: [number, number] = [16.0474546, 108.1992956]; // Da Nang
    const center = userLocation ? [userLocation.lat, userLocation.lng] as [number, number] : defaultCenter;

    return (
        <div className="map-container">
            <MapContainer center={center} zoom={13} scrollWheelZoom={true}>
                <ChangeView center={center} zoom={13} />
                <MapResizeHandler />
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {userLocation && (
                    <Marker position={[userLocation.lat, userLocation.lng]} icon={UserIcon}>
                        <Popup>{t('map.your_location')}</Popup>
                    </Marker>
                )}
                {facilities.map((facility, index) => (
                    <Marker
                        key={facility.id}
                        position={[facility.lat, facility.lng]}
                        icon={index === 0 ? DestinationIcon : FacilityIcon}
                    >
                        <Popup className="facility-popup">
                            <div className="popup-content">
                                <h3 className="popup-title">{facility.name}</h3>
                                <p className="popup-type">{facility.type}</p>

                                {facility.address && (
                                    <div className="popup-row">
                                        <MapPin className="popup-icon" />
                                        <span>{facility.address}</span>
                                    </div>
                                )}

                                <div className="popup-actions">
                                    <button
                                        className="popup-btn primary"
                                        onClick={() => onDirections?.(facility)}
                                        title={t('map.tooltip_directions')}
                                    >
                                        <Navigation className="w-4 h-4" />
                                    </button>

                                    {facility.phone && (
                                        <button
                                            className="popup-btn"
                                            onClick={() => onCall?.(facility.phone!)}
                                            title={t('map.tooltip_call')}
                                        >
                                            <Phone className="w-4 h-4" />
                                        </button>
                                    )}

                                    {facility.website && (
                                        <button
                                            className="popup-btn"
                                            onClick={() => onWebsite?.(facility.website!)}
                                            title={t('map.tooltip_website')}
                                        >
                                            <Globe className="w-4 h-4" />
                                        </button>
                                    )}

                                    <button
                                        className="popup-btn"
                                        onClick={() => onShare?.(facility)}
                                        title={t('map.tooltip_share')}
                                    >
                                        <Share2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        </Popup>
                    </Marker>
                ))}
                {routeGeometry && (
                    <Polyline
                        positions={routeGeometry}
                        color="#009688"
                        weight={5}
                        opacity={0.8}
                    />
                )}
            </MapContainer>
        </div>
    );
};

export default MapView;
