import apiClient from './api';

export const searchFirstAidGuides = async (params: any) => {
  // Backend expects 'wound_type', 'severity', 'limit', 'offset' in params
  // If 'searchTerm' is passed, we might need to map it to 'wound_type' or handle it differently
  // For now, assuming params are correctly structured or just passing them through
  const response = await apiClient.get('/first-aid/search', { params });
  return response.data;
};

export const getWoundTypes = async () => {
  const response = await apiClient.get('/first-aid/wound-types');
  return response.data;
};

export const getFirstAidStatistics = async () => {
  const response = await apiClient.get('/first-aid/statistics');
  return response.data;
};

export const createFirstAidGuide = async (data: any) => {
  const response = await apiClient.post('/first-aid/guides', data);
  return response.data;
};

export const updateFirstAidGuide = async (id: string, data: any) => {
  const response = await apiClient.put(`/first-aid/guides/${id}`, data);
  return response.data;
};

export const deleteFirstAidGuide = async (id: string, softDelete = true) => {
  // Backend expects 'hard_delete' (boolean), not 'soft_delete'
  // If softDelete is true, then hard_delete should be false
  const hardDelete = !softDelete;
  const response = await apiClient.delete(`/first-aid/guides/${id}`, { params: { hard_delete: hardDelete } });
  return response.data;
};
