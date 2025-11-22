import apiClient from './api';
import type { ApiResponse } from '../types/admin';

export interface AuditLog {
    audit_action_id: string;
    user_id: string | null;
    action: string;
    resource_type: string | null;
    resource_id: string | null;
    ip_address: string | null;
    user_agent: string | null;
    success: boolean;
    error_message: string | null;
    is_guest: boolean;
    guest_session_id: string | null;
    details: Record<string, any> | null;
    timestamp: string;
}

export interface AuditLogListResponse {
    logs: AuditLog[];
    total: number;
    page: number;
    limit: number;
    total_pages: number;
    has_more: boolean;
}

export interface AuditLogFilterParams {
    page?: number;
    limit?: number;
    offset?: number;
    user_id?: string;
    action?: string;
    resource_type?: string;
    success?: boolean;
    is_guest?: boolean;
    search?: string;
    role_name?: string;
    start_date?: string;
    end_date?: string;
}

/**
 * Get audit logs with filtering and pagination
 */
export const getAuditLogs = async (params: AuditLogFilterParams = {}): Promise<ApiResponse<AuditLogListResponse>> => {
    const queryParams = new URLSearchParams();

    if (params.page) queryParams.append('page', params.page.toString());
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.offset !== undefined) queryParams.append('offset', params.offset.toString());
    if (params.user_id) queryParams.append('user_id', params.user_id);
    if (params.action && params.action !== 'all') queryParams.append('action', params.action);
    if (params.resource_type) queryParams.append('resource_type', params.resource_type);
    if (params.success !== undefined) queryParams.append('success', params.success.toString());
    if (params.is_guest !== undefined) queryParams.append('is_guest', params.is_guest.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.role_name) queryParams.append('role_name', params.role_name);
    if (params.start_date) queryParams.append('start_date', params.start_date);
    if (params.end_date) queryParams.append('end_date', params.end_date);

    const response = await apiClient.get(`/audit/logs?${queryParams.toString()}`);
    return response.data;
};

/**
 * Get audit statistics
 */
export const getAuditStats = async (): Promise<ApiResponse<any>> => {
    const response = await apiClient.get('/audit/stats');
    return response.data;
};
