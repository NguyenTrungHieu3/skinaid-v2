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
  const response = await apiClient.get("/users", {
    params: {
      page: params.page,
      limit: params.page_size,
      search: params.search,
      role: params.role,
      status: params.status,
    },
  });

  // Backend returns SuccessResponse: { success, message, data: { users, pagination } }
  const raw = response.data;
  const payload = raw.data || raw;

  // Map backend UserBasicInfo → frontend UserListItem
  const users = payload.users || payload.items || [];
  const pagination = payload.pagination || {};

  return {
    total: pagination.total ?? payload.total ?? 0,
    page: pagination.page ?? params.page ?? 1,
    page_size: pagination.limit ?? params.page_size ?? 10,
    items: users.map((u: any) => ({
      id: u.user_id || u.id,
      full_name: u.display_name || u.full_name || null,
      email: u.email,
      role: (u.roles && u.roles.length > 0) ? u.roles[0] : (u.role || 'user'),
      status: u.is_active === false ? 'inactive' : (u.status || 'active'),
      uploads_count: u.upload_count ?? u.uploads_count ?? 0,
      join_date: u.created_at || '',
      last_active_at: u.last_active_at || u.last_login || null,
    })),
  };
};

/**
 * Fetch detailed user information including scan history
 */
export const getUserDetail = async (userId: string): Promise<UserDetail> => {
  const response = await apiClient.get(`/users/${userId}`);

  // Backend: SuccessResponse { data: { user: UserDetailInfo } }
  const raw = response.data;
  const payload = raw.data?.user || raw.data || raw;

  return {
    id: payload.user_id || payload.id || userId,
    full_name: payload.display_name || payload.full_name || null,
    email: payload.email,
    role: (payload.roles && payload.roles.length > 0) ? payload.roles[0] : (payload.role || 'user'),
    status: payload.is_active === false ? 'inactive' : (payload.status || 'active'),
    uploads_count: payload.upload_count ?? payload.uploads_count ?? 0,
    join_date: payload.created_at || '',
    last_active_at: payload.last_active_at || payload.last_login || null,
    scan_history: payload.scan_history || [],
  };
};

/**
 * Update user status to active or inactive
 */
export const updateUserStatus = async (
  userId: string,
  status: "active" | "inactive"
): Promise<UpdateStatusResponse> => {
  const response = await apiClient.patch(
    `/users/${userId}/status`,
    { is_active: status === "active" }
  );

  const raw = response.data;
  const payload = raw.data?.user || raw.data || raw;

  return {
    id: payload.user_id || payload.id || userId,
    status: payload.is_active === false ? 'inactive' : 'active',
    updated_at: payload.updated_at || new Date().toISOString(),
  };
};
