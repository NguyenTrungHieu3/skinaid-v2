import apiClient from './api';

// Types for First Aid Guide
export interface FirstAidGuideSource {
  name: string;
  url?: string;
}

export interface FirstAidGuideSearchParams {
  wound_type?: string;
  severity?: string;
  is_active?: boolean;
  search?: string;
  limit?: number;
  offset?: number;
}

export interface FirstAidGuideCreateData {
  wound_type: string;
  severity: string;
  sub_type?: string;
  title: string;
  description?: string;
  steps: string[];
  dos?: string[];
  donts?: string[];
  supplies_needed?: string[];
  estimated_healing_time?: string;
  source: FirstAidGuideSource;
  is_active?: boolean;
}

export interface FirstAidGuideUpdateData {
  title?: string;
  description?: string;
  steps?: string[];
  dos?: string[];
  donts?: string[];
  supplies_needed?: string[];
  estimated_healing_time?: string;
  source?: FirstAidGuideSource;
  is_active?: boolean;
  sub_type?: string;
}

export const searchFirstAidGuides = async (params: FirstAidGuideSearchParams) => {
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

export const createFirstAidGuide = async (data: FirstAidGuideCreateData) => {
  const response = await apiClient.post('/first-aid/guides', data);
  return response.data;
};

export const updateFirstAidGuide = async (id: string, data: FirstAidGuideUpdateData) => {
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
