import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance for user management
const userAPI = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
userAPI.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle response errors
userAPI.interceptors.response.use(
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
 * Get paginated list of users with filters
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number (starts from 1)
 * @param {number} params.limit - Records per page
 * @param {string} params.search - Search term for email/display name
 * @param {string} params.role - Filter by role (user, moderator, admin)
 * @param {string} params.status - Filter by status (active, inactive)
 */
export const getUsers = async (params = {}) => {
  try {
    const { page = 1, limit = 10, search = '', role = '', status = '' } = params;
    const queryParams = new URLSearchParams();
    
    queryParams.append('page', page.toString());
    queryParams.append('limit', limit.toString());
    if (search) queryParams.append('search', search);
    if (role) queryParams.append('role', role);
    if (status) queryParams.append('status', status);
    
    const response = await userAPI.get(`/api/v1/admin/users?${queryParams.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch users:', error);
    throw error;
  }
};

/**
 * Get user statistics
 */
export const getUserStats = async () => {
  try {
    const response = await userAPI.get('/api/v1/admin/users/stats');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch user stats:', error);
    throw error;
  }
};

/**
 * Get detailed information about a specific user
 * @param {string} userId - User ID
 */
export const getUserDetail = async (userId) => {
  try {
    const response = await userAPI.get(`/api/v1/admin/users/${userId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch user detail:', error);
    throw error;
  }
};

/**
 * Create a new user
 * @param {Object} userData - User data
 * @param {string} userData.email - User email
 * @param {string} userData.display_name - Display name
 * @param {string} userData.password - Password
 * @param {string} userData.role - Role (user, moderator, admin)
 */
export const createUser = async (userData) => {
  try {
    const response = await userAPI.post('/api/v1/admin/users', userData);
    return response.data;
  } catch (error) {
    console.error('Failed to create user:', error);
    throw error;
  }
};

/**
 * Update user information
 * @param {string} userId - User ID
 * @param {Object} userData - Update data (partial)
 */
export const updateUser = async (userId, userData) => {
  try {
    const response = await userAPI.put(`/api/v1/admin/users/${userId}`, userData);
    return response.data;
  } catch (error) {
    console.error('Failed to update user:', error);
    throw error;
  }
};

/**
 * Update user status (active/inactive)
 * @param {string} userId - User ID
 * @param {boolean} isActive - New status
 */
export const updateUserStatus = async (userId, isActive) => {
  try {
    const response = await userAPI.patch(`/api/v1/admin/users/${userId}/status`, {
      is_active: isActive
    });
    return response.data;
  } catch (error) {
    console.error('Failed to update user status:', error);
    throw error;
  }
};

/**
 * Delete a user (soft delete)
 * @param {string} userId - User ID
 */
export const deleteUser = async (userId) => {
  try {
    const response = await userAPI.delete(`/api/v1/admin/users/${userId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to delete user:', error);
    throw error;
  }
};

/**
 * Resend verification email to unverified user
 * @param {string} userId - User ID
 */
export const resendVerificationEmail = async (userId) => {
  try {
    const response = await userAPI.post(`/api/v1/admin/users/${userId}/resend-verification`);
    return response.data;
  } catch (error) {
    console.error('Failed to resend verification email:', error);
    throw error;
  }
};

/**
 * Check user management service health
 */
export const checkUserManagementHealth = async () => {
  try {
    const response = await userAPI.get('/api/v1/admin/users/health/check');
    return response.data;
  } catch (error) {
    console.error('User management health check failed:', error);
    throw error;
  }
};

export default userAPI;
