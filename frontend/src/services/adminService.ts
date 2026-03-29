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
 * @param period - Time period for statistics (day, week, month, year, all)
 * @returns Promise containing dashboard overview data
 */
export const getDashboardOverview = async (period = 'month'): Promise<ApiResponse<DashboardOverview>> => {
  // Endpoint changed from /admin/dashboard/overview to /dashboard/overview
  const response = await apiClient.get(`/dashboard/overview?period=${period}`);
  return response.data;
};

/**
 * Get wound type distribution
 * @param period - Time period for statistics (day, week, month, year, all)
 * @returns Promise containing wound type distribution data
 */
export const getWoundTypeDistribution = async (period = 'month'): Promise<ApiResponse<WoundTypeDistributionResponse>> => {
  // Endpoint changed from /admin/wound-types/distribution to /dashboard/wound-types/distribution
  const response = await apiClient.get(`/dashboard/wound-types/distribution?period=${period}`);
  return response.data;
};

/**
 * Get severity statistics
 * @param period - Time period for statistics (day, week, month, year, all)
 * @returns Promise containing severity stats
 */
export const getSeverityStats = async (period = 'month'): Promise<ApiResponse<SeverityStatsResponse>> => {
  // Endpoint changed from /admin/severity/stats to /dashboard/severity/stats
  const response = await apiClient.get(`/dashboard/severity/stats?period=${period}`);
  return response.data;
};

/**
 * Get weekly activity statistics
 * @returns Promise containing weekly activity data
 */
export const getWeeklyActivity = async (): Promise<ApiResponse<{ daily_stats: any[]; total_uploads: number; total_analyses: number }>> => {
  // New endpoint for weekly activity
  const response = await apiClient.get(`/dashboard/activity/weekly`);
  return response.data;
};

/**
 * Get system logs
 * @param limit - Number of logs to retrieve (default: 10)
 * @returns Promise containing system log entries
 */
export const getSystemLogs = async (limit = 10): Promise<ApiResponse<SystemLogsResponse>> => {
  // Endpoint changed from /admin/logs/recent to /dashboard/logs/recent
  const response = await apiClient.get(`/dashboard/logs/recent?limit=${limit}`);
  return response.data;
};
