import apiClient from './api';

// Types for User Management
export interface UserSearchParams {
  search?: string;
  role?: string;
  status?: boolean | string;
  page?: number;
  limit?: number;
}

export interface CreateUserData {
  email: string;
  user_name: string;
  password: string;
  role: string;
}

export interface UpdateUserData {
  email?: string;
  user_name?: string;
  password?: string;
  role?: string;
}

export const getUsers = async (params: UserSearchParams) => {
  const response = await apiClient.get('/admin/users', { params });
  return response.data;
};

export const createUser = async (data: CreateUserData) => {
  const response = await apiClient.post('/admin/users', data);
  return response.data;
};

export const updateUser = async (userId: string, data: UpdateUserData) => {
  const response = await apiClient.put(`/admin/users/${userId}`, data);
  return response.data;
};

export const updateUserStatus = async (userId: string, status: boolean) => {
  const response = await apiClient.patch(`/admin/users/${userId}/status`, { is_active: status });
  return response.data;
};

export const deleteUser = async (userId: string) => {
  const response = await apiClient.delete(`/admin/users/${userId}`);
  return response.data;
};
