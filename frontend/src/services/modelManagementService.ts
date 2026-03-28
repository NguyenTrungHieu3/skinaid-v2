import apiClient from './api';
import type {
  ApiResponse,
  ModelListResponse,
  ModelDetailResponse,
  ModelUploadResponse,
  ModelActivateResponse,
  ModelRollbackResponse,
  ModelDeleteResponse,
  ModelUploadRequest,
} from '../types/admin';

/**
 * Model Management Service (PBI-27)
 *
 * Handles all AI model lifecycle operations:
 * - Upload new models
 * - List and query models
 * - Activate/deactivate versions
 * - Rollback to previous versions
 * - Delete models
 * - View metadata and metrics
 * - Runtime status monitoring
 */

const BASE_URL = '/admin/models';

/**
 * List all AI models with filtering
 * @param modelType - Filter by model type
 * @param status - Filter by status (active, inactive, deprecated, all)
 * @param includeBeta - Include beta versions
 * @param search - Search term
 * @returns Promise containing model list
 */
export const listModels = async (
  modelType?: string,
  status: string = 'all',
  includeBeta: boolean = true,
  search?: string
): Promise<ApiResponse<ModelListResponse>> => {
  const params = new URLSearchParams();
  if (modelType) params.append('model_type', modelType);
  if (status) params.append('status', status);
  params.append('include_beta', includeBeta.toString());
  if (search) params.append('search', search);

  const response = await apiClient.get(`${BASE_URL}?${params.toString()}`);
  return response.data;
};

/**
 * Get detailed model information
 * @param modelId - Model UUID
 * @returns Promise containing model details
 */
export const getModelDetail = async (modelId: string): Promise<ApiResponse<ModelDetailResponse>> => {
  const response = await apiClient.get(`${BASE_URL}/${modelId}`);
  return response.data;
};

/**
 * Get model versions
 * @param modelId - Model UUID
 * @returns Promise containing version list
 */
export const getModelVersions = async (modelId: string): Promise<ApiResponse<any>> => {
  const response = await apiClient.get(`${BASE_URL}/${modelId}/versions`);
  return response.data;
};

/**
 * Upload a new model version
 * @param file - Model file to upload
 * @param data - Upload request data
 * @param onProgress - Upload progress callback
 * @returns Promise containing upload response
 */
export const uploadModel = async (
  file: File,
  data: ModelUploadRequest,
  onProgress?: (progress: number) => void
): Promise<ApiResponse<ModelUploadResponse>> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('model_type', data.model_type);
  formData.append('version_tag', data.version_tag);
  if (data.description) formData.append('description', data.description);
  formData.append('is_beta', data.is_beta.toString());

  const response = await apiClient.post(`${BASE_URL}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    },
  });
  return response.data;
};

/**
 * Activate a model version
 * @param modelId - Model UUID to activate
 * @param force - Force activation even if validation fails
 * @returns Promise containing activation response
 */
export const activateModel = async (
  modelId: string,
  force: boolean = false
): Promise<ApiResponse<ModelActivateResponse>> => {
  const response = await apiClient.post(`${BASE_URL}/${modelId}/activate`, null, {
    params: { force },
  });
  return response.data;
};

/**
 * Rollback to a previous model version
 * @param modelId - Current model UUID
 * @param targetVersion - Specific version to rollback to (optional)
 * @param reason - Reason for rollback
 * @returns Promise containing rollback response
 */
export const rollbackModel = async (
  modelType: string,
  reason?: string
): Promise<ApiResponse<ModelRollbackResponse>> => {
  const params: any = {};
  if (reason) params.reason = reason;

  const response = await apiClient.post(`${BASE_URL}/types/${modelType}/rollback`, null, { params });
  return response.data;
};

/**
 * Delete a model version (soft delete)
 * @param modelId - Model UUID to delete
 * @param reason - Reason for deletion
 * @returns Promise containing delete response
 */
export const deleteModel = async (
  modelId: string,
  reason?: string
): Promise<ApiResponse<ModelDeleteResponse>> => {
  const response = await apiClient.delete(`${BASE_URL}/${modelId}`, {
    params: { reason },
  });
  return response.data;
};

/**
 * Deactivate a model version
 * @param modelId - Model UUID to deactivate
 * @returns Promise containing deactivate response
 */
export const deactivateModel = async (
  modelId: string
): Promise<ApiResponse<any>> => {
  const response = await apiClient.post(`${BASE_URL}/${modelId}/deactivate`);
  return response.data;
};

/**
 * Get model metadata
 * @param modelId - Model UUID
 * @returns Promise containing model metadata
 */
export const getModelMetadata = async (modelId: string): Promise<ApiResponse<any>> => {
  const response = await apiClient.get(`${BASE_URL}/${modelId}/metadata`);
  return response.data;
};

/**
 * Update model metadata
 * @param modelId - Model UUID
 * @param data - Metadata update data
 * @returns Promise containing updated metadata
 */
export const updateModelMetadata = async (
  modelId: string,
  data: { description?: string; is_beta?: boolean }
): Promise<ApiResponse<any>> => {
  const response = await apiClient.put(`${BASE_URL}/${modelId}/metadata`, data);
  return response.data;
};

/**
 * Get runtime status of all models
 * @returns Promise containing runtime health status
 */
export const getRuntimeStatus = async (): Promise<ApiResponse<any>> => {
  const response = await apiClient.get(`${BASE_URL}/runtime/status`);
  return response.data;
};

/**
 * Reload a model at runtime (internal API)
 * @param modelType - Model type to reload
 * @param versionTag - Specific version to load
 * @param apiKey - Internal API key
 * @returns Promise containing reload response
 */
export const reloadModel = async (
  modelType: string,
  versionTag: string,
  apiKey: string
): Promise<ApiResponse<any>> => {
  const response = await apiClient.post(`${BASE_URL}/runtime/reload`, {
    model_type: modelType,
    version_tag: versionTag,
    api_key: apiKey,
  });
  return response.data;
};

/**
 * Get model audit logs
 * @param modelId - Model UUID
 * @param limit - Number of logs to retrieve
 * @returns Promise containing audit logs
 */
export const getModelLogs = async (
  modelId: string,
  limit: number = 50
): Promise<ApiResponse<any>> => {
  const response = await apiClient.get(`${BASE_URL}/${modelId}/logs`, {
    params: { limit },
  });
  return response.data;
};
