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
 * Updated to use new dashboard endpoint
 */
export const getAuditLogs = async (params: AuditLogFilterParams = {}): Promise<ApiResponse<AuditLogListResponse>> => {
    const queryParams = new URLSearchParams();

    if (params.limit) queryParams.append('limit', params.limit.toString());
    
    // Use new dashboard endpoint
    const response = await apiClient.get(`/dashboard/logs/recent?${queryParams.toString()}`);
    return response.data;
};

/**
 * Get audit statistics
 */
export const getAuditStats = async (): Promise<ApiResponse<any>> => {
    const response = await apiClient.get('/audit/stats');
    return response.data;
};
