import apiClient from "./api";

// ---------------------------------------------------------------------------
// TYPES & INTERFACES (kept as-is for frontend compatibility)
// ---------------------------------------------------------------------------

export interface UserListItem {
  id: string; // Mapped from backend's user_id
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
  page_size?: number; // Will be mapped to backend's "limit"
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
// BACKEND RESPONSE TYPES (what the API actually returns)
// ---------------------------------------------------------------------------

interface BackendUserBasicInfo {
  user_id: string;
  email: string;
  user_name: string;
  display_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  roles: string[];
  upload_count: number;
}

interface BackendUserDetailInfo extends BackendUserBasicInfo {
  updated_at: string;
  last_login: string | null;
}

interface BackendPaginationInfo {
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

interface BackendUserListData {
  users: BackendUserBasicInfo[];
  pagination: BackendPaginationInfo;
}

interface BackendUserDetailData {
  user: BackendUserDetailInfo;
}

/** Generic wrapper for all backend responses */
interface BackendSuccessResponse<T> {
  success: boolean;
  message: string;
  data: T;
  timestamp: string;
  status_code: number;
}

// ---------------------------------------------------------------------------
// MAPPERS
// ---------------------------------------------------------------------------

/** Map a backend user object to the frontend's UserListItem shape */
function mapToUserListItem(u: BackendUserBasicInfo): UserListItem {
  return {
    id: u.user_id,
    full_name: u.display_name ?? u.user_name ?? null,
    email: u.email,
    role: u.roles?.length ? u.roles[0] : "user",
    status: u.is_active ? "active" : "inactive",
    uploads_count: u.upload_count ?? 0,
    join_date: u.created_at,
    last_active_at: null, // Not provided by backend list endpoint
  };
}

/** Map a backend detail object to the frontend's UserDetail shape */
function mapToUserDetail(u: BackendUserDetailInfo): UserDetail {
  return {
    id: u.user_id,
    full_name: u.display_name ?? u.user_name ?? null,
    email: u.email,
    role: u.roles?.length ? u.roles[0] : "user",
    status: u.is_active ? "active" : "inactive",
    uploads_count: u.upload_count ?? 0,
    join_date: u.created_at,
    last_active_at: u.last_login ?? null,
    scan_history: [], // Backend doesn't return scan history in this endpoint
  };
}

// ---------------------------------------------------------------------------
// SERVICE FUNCTIONS
// ---------------------------------------------------------------------------

/**
 * Fetch list of users with pagination and filtering
 */
export const getUsers = async (params: GetUsersParams): Promise<GetUsersResponse> => {
  // Map frontend param names to backend param names
  const backendParams: Record<string, any> = {};
  if (params.page) backendParams.page = params.page;
  if (params.page_size) backendParams.limit = params.page_size; // page_size → limit
  if (params.search) backendParams.search = params.search;
  if (params.role) backendParams.role = params.role;
  if (params.status) backendParams.status = params.status;

  const response = await apiClient.get<BackendSuccessResponse<BackendUserListData>>(
    "/admin/users",
    { params: backendParams }
  );

  const backendData = response.data.data;
  
  return {
    total: backendData?.pagination?.total ?? 0,
    page: backendData?.pagination?.page ?? 1,
    page_size: backendData?.pagination?.limit ?? 10,
    items: (backendData?.users ?? []).map(mapToUserListItem),
  };
};

/**
 * Fetch detailed user information including scan history
 */
export const getUserDetail = async (userId: string): Promise<UserDetail> => {
  const response = await apiClient.get<BackendSuccessResponse<BackendUserDetailData>>(
    `/admin/users/${userId}`
  );

  const backendUser = response.data.data?.user;
  if (!backendUser) {
    throw new Error("User not found");
  }

  return mapToUserDetail(backendUser);
};

/**
 * Update user status to active or inactive
 */
export const updateUserStatus = async (
  userId: string,
  status: "active" | "inactive"
): Promise<UpdateStatusResponse> => {
  // Backend expects { is_active: boolean }, not { status: string }
  const is_active = status === "active";

  const response = await apiClient.patch<BackendSuccessResponse<BackendUserDetailData>>(
    `/admin/users/${userId}/status`,
    { is_active }
  );

  const backendUser = response.data.data?.user;

  return {
    id: backendUser?.user_id ?? userId,
    status: backendUser?.is_active ? "active" : "inactive",
    updated_at: backendUser?.updated_at ?? new Date().toISOString(),
  };
};
