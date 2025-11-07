import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const adminAPI = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
adminAPI.interceptors.request.use((config) => {
  const access_token = localStorage.getItem('token'); // Changed from 'access_token' to 'token'
  if (access_token) {
    config.headers.Authorization = `Bearer ${access_token}`;
  }
  return config;
});

// Handle response errors
adminAPI.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    // Nếu token hết hạn và chưa retry lần nào
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refreshToken');
        const res = await axios.post(`${API_BASE_URL}/auth/refresh`, { refreshToken });
        const newAccessToken = res.data.accessToken;
        localStorage.setItem('accessToken', newAccessToken);
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return adminAPI(originalRequest);
      } catch (refreshError) {
        console.error('Refresh token expired → Đăng nhập lại');
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      }
    } 

    if (error.response?.status === 401) {
      // Redirect to login if unauthorized
      localStorage.removeItem('token'); // Changed from 'access_token' to 'token'
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      window.location.href = '/signin'; // Changed from '/login' to '/signin'
    }
    return Promise.reject(error);
  }
);

// Lấy thống kê dashboard tổng quan của admin
export const getDashboardOverview = async () => {
  try {
    const response = await adminAPI.get('/api/v1/admin/dashboard/overview');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch dashboard overview:', error);
    throw error;
  }
};

// Lấy dữ liệu 3 loại vết thương cho pie chart
export const getWoundTypeDistribution = async () => {
  try {
    const response = await adminAPI.get('/api/v1/admin/wound-types/distribution');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch wound type distribution:', error);
    throw error;
  }
};

// Lấy thống kê hoạt động cho biểu đồ cột 
export const getWeeklyActivity = async () => {
  try {
    const response = await adminAPI.get('/api/v1/admin/activity/weekly');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch weekly activity:', error);
    throw error;
  }
};

// Lấy thống kê severity level (Mild, Moderate, Severe)
export const getSeverityStats = async () => {
  try {
    const response = await adminAPI.get('/api/v1/admin/severity/stats');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch severity stats:', error);
    throw error;
  }
};

// Lấy log của hệ thống mặc định 10 logs
export const getSystemLogs = async (limit = 10) => {
  try {
    const response = await adminAPI.get(`/api/v1/admin/logs/recent?limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch system logs:', error);
    throw error;
  }
};

// Kiểm tra trạng thái của admin api
export const checkAdminHealth = async () => {
  try {
    const response = await adminAPI.get('/api/v1/admin/health');
    return response.data;
  } catch (error) {
    console.error('Admin health check failed:', error);
    throw error;
  }
};

// Lấy dữ liệu phân quyền role 
export const getRolePermissions = () => {
  // Based on backend/app/shared/role_permission_enum.py
  return [
    {
      role: 'admin',
      displayName: 'Administrator',
      color: 'purple-pink',
      permissions: {
        canManageUsers: true,
        canEditContent: true,
        canDeleteData: true,
        canViewLogs: true,
        canManagePermissions: true,
        canUploadImage: true,
        canAIAnalyze: true,
        canViewAllHistory: true
      },
      description: 'Full system access with all permissions',
      permissionsList: [
        'CREATE_USER', 'READ_USER', 'UPDATE_USER', 'DELETE_USER',
        'CREATE_FIRSTAID', 'READ_FIRSTAID', 'UPDATE_FIRSTAID', 'DELETE_FIRSTAID',
        'UPLOAD_IMAGE', 'AI_ANALYZE',
        'READ_OWN_HISTORY', 'READ_ALL_HISTORY',
        'READ_SYSTEM_LOGS', 'MANAGE_ROLES'
      ]
    },
    {
      role: 'user',
      displayName: 'Regular User',
      color: 'cyan-blue',
      permissions: {
        canManageUsers: false,
        canEditContent: false,
        canDeleteData: false,
        canViewLogs: false,
        canManagePermissions: false,
        canUploadImage: true,
        canAIAnalyze: true,
        canViewAllHistory: false
      },
      description: 'Standard user with basic features',
      permissionsList: [
        'READ_FIRSTAID',
        'UPLOAD_IMAGE',
        'AI_ANALYZE',
        'READ_OWN_HISTORY'
      ]
    }
  ];
};


export const getPermissionDescriptions = () => {
  return {
    canManageUsers: 'Create, update, and delete user accounts',
    canEditContent: 'Modify first-aid guides and content',
    canDeleteData: 'Permanently delete data from system',
    canViewLogs: 'Access system logs and activity',
    canManagePermissions: 'Manage roles and permissions',
    canUploadImage: 'Upload wound images for analysis',
    canAIAnalyze: 'Request AI wound analysis',
    canViewAllHistory: 'View all users\' wound history'
  };
};

export default adminAPI;
