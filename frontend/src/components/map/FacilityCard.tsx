import { Phone, MapPin, Clock, Globe, Share2, Navigation } from "lucide-react";
import "./MapComponents.css";

export interface Facility {
    id: string;
    name: string;
    type: string;
    address: string;
    phone?: string;
    hours?: string;
    distance: number;
    website?: string;
    lat: number;
    lng: number;
}

interface FacilityCardProps {
    facility: Facility;
    onDirections: (facility: Facility) => void;
    onCall?: (phone: string) => void;
    onWebsite?: (url: string) => void;
    onShare?: (facility: Facility) => void;
}

const FacilityCard = ({ facility, onDirections, onCall, onWebsite, onShare }: FacilityCardProps) => {
    return (
        <div className="facility-card">
            <div className="facility-header">
                <div>
                    <h3 className="facility-name">{facility.name}</h3>
                    <p className="facility-type">{facility.type}</p>
                </div>
                <span className="facility-distance">
                    {facility.distance < 1000
                        ? `${Math.round(facility.distance)} m`
                        : `${(facility.distance / 1000).toFixed(1)} km`}
                </span>
            </div>

            <div className="facility-info">
                {facility.address && (
                    <div className="info-row">
                        <MapPin className="icon-sm address-icon" />
                        <span>{facility.address}</span>
                    </div>
                )}
                {facility.phone && (
                    <div className="info-row">
                        <Phone className="icon-sm" />
                        <span>{facility.phone}</span>
                    </div>
                )}
                {facility.hours && (
                    <div className="info-row">
                        <Clock className="icon-sm" />
                        <span>{facility.hours}</span>
                    </div>
                )}
            </div>

            <div className="facility-actions">
                {facility.phone && (
                    <button
                        className="map-btn"
                        onClick={() => onCall?.(facility.phone!)}
                    >
                        <Phone className="icon-btn" />
                        Gọi
                    </button>
                )}
                <button
                    className="map-btn primary"
                    onClick={() => onDirections(facility)}
                >
                    <Navigation className="icon-btn" />
                    Chỉ đường
                </button>
                {facility.website && (
                    <button
                        className="map-btn"
                        onClick={() => onWebsite?.(facility.website!)}
                    >
                        <Globe className="icon-btn" />
                        Website
                    </button>
                )}
                <button
                    className="map-btn"
                    onClick={() => onShare?.(facility)}
                >
                    <Share2 className="icon-btn" />
                    Chia sẻ
                </button>
            </div>
        </div>
    );
};

export default FacilityCard;
