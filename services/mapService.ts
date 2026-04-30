/**
 * mapService.ts
 * Centralized service layer for all Map-related API endpoints.
 * All requests flow through axiosClient (handles auth + token refresh).
 */

import axiosClient from "../api/axiosClient";

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

export interface IPLocation {
  latitude: number;
  longitude: number;
  city: string;
  country: string;
  accuracy: string;
  source: string;
}

export interface NearbyPlace {
  place_id: string;
  name: string;
  category: string;
  latitude: number;
  longitude: number;
  address: string;
  distance: number;
  phone: string;
  opening_hours: string;
  rating: number;
  website: string;
  marker_icon_url: string;
}

export interface RouteStep {
  instruction: string;
  distance: number;
  duration: number;
}

export interface RouteData {
  distance: number;
  duration: number;
  distance_km: number;
  duration_minutes: number;
  mode: string;
  summary: string;
  geometry: number[][];
  steps: RouteStep[];
}

export interface GeocodeResult {
  latitude: number;
  longitude: number;
  formatted_address: string;
  place_id: string;
  city: string;
  country: string;
}

export interface ReverseGeocodeResult {
  formatted_address: string;
  street: string;
  city: string;
  country: string;
  postcode: string;
}

export type TransportMode = "drive" | "walk" | "bicycle" | "transit";

// ─────────────────────────────────────────────
// API Functions
// ─────────────────────────────────────────────

/**
 * GET /api/v1/map/location/ip
 * Detect approximate location from the device's IP address.
 * Used as a fast fallback before GPS permission is granted.
 */
export const getLocationByIP = async (): Promise<IPLocation> => {
  const res = await axiosClient.get("/map/location/ip");
  return res.data.data as IPLocation;
};

/**
 * POST /api/v1/map/nearby-places
 * Find medical facilities near a given coordinate.
 */
export const getNearbyPlaces = async (params: {
  latitude: number;
  longitude: number;
  radius?: number;       // metres, default 5000
  category?: string;    // e.g. "hospital", "clinic", "dermatology"
  keyword?: string;
  limit?: number;
}): Promise<NearbyPlace[]> => {
  const res = await axiosClient.post("/map/nearby-places", {
    latitude: params.latitude,
    longitude: params.longitude,
    radius: params.radius ?? 5000,
    category: params.category ?? "hospital",
    keyword: params.keyword ?? "",
    limit: params.limit ?? 20,
  });
  return res.data.data as NearbyPlace[];
};

/**
 * POST /api/v1/map/route
 * Fields from OpenAPI spec: start_latitude, start_longitude, end_latitude, end_longitude, mode
 * mode default: "drive" (Geoapify format)
 */
export const getRoute = async (params: {
  origin_lat: number;
  origin_lng: number;
  dest_lat: number;
  dest_lng: number;
  mode?: string;
}): Promise<RouteData> => {
  const res = await axiosClient.post("/map/route", {
    start_latitude:  params.origin_lat,
    start_longitude: params.origin_lng,
    end_latitude:    params.dest_lat,
    end_longitude:   params.dest_lng,
    mode: params.mode ?? "drive",
  });
  return res.data.data as RouteData;
};

/**
 * GET /api/v1/map/geocode
 * Convert a human-readable address to coordinates.
 */
export const geocodeAddress = async (
  address: string
): Promise<GeocodeResult> => {
  const res = await axiosClient.get("/map/geocode", {
    params: { address },
  });
  return res.data.data as GeocodeResult;
};

/**
 * GET /api/v1/map/reverse-geocode
 * Convert coordinates to a human-readable address.
 */
export const reverseGeocode = async (
  latitude: number,
  longitude: number
): Promise<ReverseGeocodeResult> => {
  const res = await axiosClient.get("/map/reverse-geocode", {
    params: { latitude, longitude },
  });
  return res.data.data as ReverseGeocodeResult;
};
