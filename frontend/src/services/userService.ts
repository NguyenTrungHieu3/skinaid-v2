import apiClient from "./api";

// ---------------------------------------------------------------------------
// TYPES & INTERFACES
// ---------------------------------------------------------------------------

export interface UserListItem {
  id: string; // Returns user_id as id in API schemas
  full_name: string | null;
  email: string;
  role: string;
  status: string; // "active" | "inactive"
  uploads_count: number;
  join_date: string; // ISO DateTime
  last_active_at: string | null; // ISO DateTime or null
}

export interface ScanHistoryItem {
  id: string;
  created_at: string;
  wound_type: string | null;
  severity: string | null;
  image_url: string | null;
}

export interface UserDetail extends UserListItem {
  scan_history: ScanHistoryItem[];
}

export interface GetUsersParams {
  search?: string;
  role?: string;
  status?: string;
  page?: number;
  page_size?: number; // Backend default is 10
}

export interface GetUsersResponse {
  total: number;
  page: number;
  page_size: number;
  items: UserListItem[];
}

export interface UpdateStatusResponse {
  id: string;
  status: string; // "active" | "inactive"
  updated_at: string;
}

// ---------------------------------------------------------------------------
// SERVICE FUNCTIONS
// ---------------------------------------------------------------------------

/**
 * Fetch list of users with pagination and filtering
 */
export const getUsers = async (params: GetUsersParams): Promise<GetUsersResponse> => {
  const response = await apiClient.get<GetUsersResponse>("/admin/users", { params });
  return response.data;
};

/**
 * Fetch detailed user information including scan history
 */
export const getUserDetail = async (userId: string): Promise<UserDetail> => {
  const response = await apiClient.get<UserDetail>(`/admin/users/${userId}`);
  return response.data;
};

/**
 * Update user status to active or inactive
 */
export const updateUserStatus = async (
  userId: string,
  status: "active" | "inactive"
): Promise<UpdateStatusResponse> => {
  const response = await apiClient.patch<UpdateStatusResponse>(
    `/admin/users/${userId}/status`,
    { status }
  );
  return response.data;
};
