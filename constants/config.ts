// constants/config.ts
// ─── App Configuration & Environment Variables ──────────────────
// Tất cả API URLs, keys, và config được quản lý tại đây.
// KHÔNG hardcode URLs/keys ở component — luôn import từ file này.

/**
 * Base URL cho backend API.
 * Production: FastAPI server trên AWS EC2.
 */
export const API_BASE_URL = "https://skinaid.xyz/api/v1";

/**
 * Geoapify API key cho bản đồ Leaflet.
 * Dùng cho: Map tiles + geocoding.
 */
export const GEOAPIFY_API_KEY = "e9e9f16da4f84d62983b6862a9399985";

/**
 * API timeout (ms).
 */
export const API_TIMEOUT = 10000;

/**
 * App metadata.
 */
export const APP_NAME = "SkinAid";
export const APP_VERSION = "1.0.0";
