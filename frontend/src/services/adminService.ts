import apiClient from './api';
import type {
  ApiResponse,
  DashboardOverview,
  WoundTypeDistributionResponse,
  SeverityStatsResponse,
  SystemLogsResponse
} from '../types/admin';

/**
 * Get dashboard overview statistics
 * @returns Promise containing dashboard overview data
 */
export const getDashboardOverview = async (period = 'month'): Promise<ApiResponse<DashboardOverview>> => {
  const response = await apiClient.get(`/admin/dashboard/overview?period=${period}`);
  return response.data;
};

/**
 * Get wound type distribution
 * @returns Promise containing wound type distribution data
 */
export const getWoundTypeDistribution = async (period = 'month'): Promise<ApiResponse<WoundTypeDistributionResponse>> => {
  const response = await apiClient.get(`/admin/wound-types/distribution?period=${period}`);
  return response.data;
};

/**
 * Get severity statistics
 * @returns Promise containing severity stats
 */
export const getSeverityStats = async (period = 'month'): Promise<ApiResponse<SeverityStatsResponse>> => {
  const response = await apiClient.get(`/admin/severity/stats?period=${period}`);
  return response.data;
};

/**
 * Get system logs
 * @param limit - Number of logs to retrieve (default: 10)
 * @returns Promise containing system log entries
 */
export const getSystemLogs = async (limit = 10): Promise<ApiResponse<SystemLogsResponse>> => {
  const response = await apiClient.get(`/admin/logs/recent?limit=${limit}`);
  return response.data;
};
