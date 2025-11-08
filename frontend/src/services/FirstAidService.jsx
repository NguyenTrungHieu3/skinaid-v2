import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance for first aid management
const firstAidAPI = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
firstAidAPI.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle response errors
firstAidAPI.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login if unauthorized
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      window.location.href = '/signin';
    }
    return Promise.reject(error);
  }
);

/**
 * Search first aid guides with filters
 * @param {Object} params - Query parameters
 * @param {string} params.wound_type - Filter by wound type (abrasion, bruise, burn, cut)
 * @param {string} params.severity - Filter by severity (mild, moderate, severe)
 * @param {number} params.limit - Records per page
 * @param {number} params.offset - Records to skip
 */
export const searchFirstAidGuides = async (params = {}) => {
  try {
    const { wound_type = '', severity = '', limit = 20, offset = 0 } = params;
    const queryParams = new URLSearchParams();
    
    if (wound_type) queryParams.append('wound_type', wound_type);
    if (severity) queryParams.append('severity', severity);
    queryParams.append('limit', limit.toString());
    queryParams.append('offset', offset.toString());
    
    const response = await firstAidAPI.get(`/api/v1/first-aid/search?${queryParams.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Failed to search first aid guides:', error);
    throw error;
  }
};

/**
 * Get first aid guide for specific wound type and severity
 * @param {string} woundType - Wound type (abrasion, bruise, burn, cut)
 * @param {string} severity - Severity level (mild, moderate, severe)
 * @param {string} subType - Sub type (only for burn: blister, skintear)
 */
export const getFirstAidGuide = async (woundType, severity, subType = null) => {
  try {
    let url = `/api/v1/first-aid/guide/${woundType}/${severity}`;
    if (subType) {
      url += `?sub_type=${subType}`;
    }
    const response = await firstAidAPI.get(url);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch first aid guide:', error);
    throw error;
  }
};

/**
 * Get available wound types with their severity levels
 */
export const getWoundTypes = async () => {
  try {
    const response = await firstAidAPI.get('/api/v1/first-aid/wound-types');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch wound types:', error);
    throw error;
  }
};

/**
 * Get first aid statistics
 */
export const getFirstAidStatistics = async () => {
  try {
    const response = await firstAidAPI.get('/api/v1/first-aid/statistics');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch first aid statistics:', error);
    throw error;
  }
};

/**
 * Validate guide availability
 * @param {string} woundType - Wound type
 * @param {string} severity - Severity level
 * @param {string} subType - Sub type (optional)
 */
export const validateGuideAvailability = async (woundType, severity, subType = null) => {
  try {
    let url = `/api/v1/first-aid/validate/${woundType}/${severity}`;
    if (subType) {
      url += `?sub_type=${subType}`;
    }
    const response = await firstAidAPI.get(url);
    return response.data;
  } catch (error) {
    console.error('Failed to validate guide availability:', error);
    throw error;
  }
};

/**
 * Get guide by ID
 * @param {string} guideId - Guide ID (UUID)
 */
export const getGuideById = async (guideId) => {
  try {
    const response = await firstAidAPI.get(`/api/v1/first-aid/guides/${guideId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch guide by ID:', error);
    throw error;
  }
};

/**
 * Create new first aid guide (Admin only)
 * @param {Object} guideData - Guide data
 * @param {string} guideData.wound_type - Wound type (abrasion, bruise, burn, cut)
 * @param {string} guideData.severity - Severity (mild, moderate, severe)
 * @param {string} guideData.sub_type - Sub type (optional, for burn: blister, skintear)
 * @param {string} guideData.title - Title
 * @param {string} guideData.description - Description (optional)
 * @param {Array<string>} guideData.steps - Steps array
 * @param {Array<string>} guideData.warnings - Warnings array (optional)
 * @param {Array<string>} guideData.dos - Do's array (optional)
 * @param {Array<string>} guideData.donts - Don'ts array (optional)
 * @param {Array<string>} guideData.supplies_needed - Supplies array (optional)
 * @param {string} guideData.estimated_healing_time - Healing time (optional)
 */
export const createFirstAidGuide = async (guideData) => {
  try {
    const response = await firstAidAPI.post('/api/v1/first-aid/guides', guideData);
    return response.data;
  } catch (error) {
    console.error('Failed to create first aid guide:', error);
    throw error;
  }
};

/**
 * Update first aid guide (Admin only)
 * @param {string} guideId - Guide ID (UUID)
 * @param {Object} updateData - Update data (partial)
 */
export const updateFirstAidGuide = async (guideId, updateData) => {
  try {
    const response = await firstAidAPI.put(`/api/v1/first-aid/guides/${guideId}`, updateData);
    return response.data;
  } catch (error) {
    console.error('Failed to update first aid guide:', error);
    throw error;
  }
};

/**
 * Delete first aid guide (Admin only)
 * @param {string} guideId - Guide ID (UUID)
 * @param {boolean} hardDelete - True for permanent delete, false for soft delete
 */
export const deleteFirstAidGuide = async (guideId, hardDelete = false) => {
  try {
    const response = await firstAidAPI.delete(
      `/api/v1/first-aid/guides/${guideId}?hard_delete=${hardDelete}`
    );
    return response.data;
  } catch (error) {
    console.error('Failed to delete first aid guide:', error);
    throw error;
  }
};

export default firstAidAPI;
