import apiClient from './api';

export const getUsers = async (params: any) => {
  const response = await apiClient.get('/admin/users', { params });
  return response.data;
};

export const createUser = async (data: any) => {
  const response = await apiClient.post('/admin/users', data);
  return response.data;
};

export const updateUser = async (userId: string, data: any) => {
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
