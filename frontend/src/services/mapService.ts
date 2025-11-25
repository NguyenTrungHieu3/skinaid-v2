import apiClient from "./api";

export interface LocationResponse {
    latitude: number;
    longitude: number;
    city?: string;
    country?: string;
    accuracy: string;
    source: string;
}

export interface PlaceResponse {
    place_id: string;
    name: string;
    category: string;
    latitude: number;
    longitude: number;
    address: string;
    distance: number;
    phone?: string;
    opening_hours?: string;
    rating?: number;
    website?: string;
    marker_icon_url: string;
}

export interface NearbyPlacesRequest {
    latitude: number;
    longitude: number;
    category?: string;
    radius?: number;
    limit?: number;
}

export interface RouteStep {
    instruction: string;
    distance: number;
    duration: number;
}

export interface RouteResponse {
    distance: number;
    duration: number;
    distance_km: number;
    duration_minutes: number;
    mode: string;
    summary: string;
    geometry: number[][]; // [[lat, lon], ...]
    steps: RouteStep[];
}

export interface RouteRequest {
    start_latitude: number;
    start_longitude: number;
    end_latitude: number;
    end_longitude: number;
    mode?: "drive" | "walk" | "bike";
}

export interface GeocodeResponse {
    latitude: number;
    longitude: number;
    formatted_address: string;
    place_id: string;
    city?: string;
    country?: string;
}

export interface ReverseGeocodeResponse {
    formatted_address: string;
    street?: string;
    city?: string;
    country?: string;
    postcode?: string;
}

const mapService = {
    getIpLocation: async (): Promise<LocationResponse> => {
        const response = await apiClient.get<LocationResponse>("/map/ip-location");
        return response.data;
    },

    findNearbyPlaces: async (request: NearbyPlacesRequest): Promise<PlaceResponse[]> => {
        const response = await apiClient.post<PlaceResponse[]>("/map/nearby-places", request);
        return response.data;
    },

    calculateRoute: async (request: RouteRequest): Promise<RouteResponse> => {
        const response = await apiClient.post<RouteResponse>("/map/route", request);
        return response.data;
    },

    geocodeAddress: async (address: string): Promise<GeocodeResponse> => {
        const response = await apiClient.get<GeocodeResponse>("/map/geocode", {
            params: { address },
        });
        return response.data;
    },

    reverseGeocode: async (latitude: number, longitude: number): Promise<ReverseGeocodeResponse> => {
        const response = await apiClient.get<ReverseGeocodeResponse>("/map/reverse-geocode", {
            params: { latitude, longitude },
        });
        return response.data;
    },
};

export default mapService;
