import apiClient from './api';

// ── Types ──────────────────────────────────────────────────────────────

export interface RagDocument {
  rag_document_id: string;
  file_name: string;
  file_type: string;
  status: 'pending' | 'indexing' | 'indexed' | 'failed' | 'deleted';
  chunk_count: number;
  error_message: string | null;
  doc_metadata: Record<string, unknown> | null;
  uploaded_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface RagDocumentListData {
  items: RagDocument[];
  total: number;
  skip: number;
  limit: number;
}

export interface RagDocumentDeleteData {
  rag_document_id: string;
  file_name: string;
  vectors_deleted: number;
  message: string;
}

export interface RagHealthData {
  collection_name: string;
  status: string;
  points_count: number;
  vectors_count: number | null;
  qdrant_connected: boolean;
}

interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  status_code?: number;
}

// ── Params ─────────────────────────────────────────────────────────────

export interface ListRagDocumentsParams {
  skip?: number;
  limit?: number;
  status?: string;
  file_type?: string;
}

// ── API Functions ──────────────────────────────────────────────────────

/**
 * Lấy danh sách tài liệu RAG với phân trang và filter.
 */
export const getRagDocuments = async (
  params: ListRagDocumentsParams = {}
): Promise<ApiResponse<RagDocumentListData>> => {
  const queryParams = new URLSearchParams();

  if (params.skip !== undefined) queryParams.append('skip', String(params.skip));
  if (params.limit !== undefined) queryParams.append('limit', String(params.limit));
  if (params.status && params.status !== 'all') queryParams.append('status', params.status);
  if (params.file_type && params.file_type !== 'all') queryParams.append('file_type', params.file_type);

  const queryString = queryParams.toString();
  const url = `/rag/documents${queryString ? `?${queryString}` : ''}`;

  const response = await apiClient.get(url);
  return response.data;
};

/**
 * Lấy chi tiết một tài liệu RAG theo ID.
 */
export const getRagDocument = async (
  docId: string
): Promise<ApiResponse<RagDocument>> => {
  const response = await apiClient.get(`/rag/documents/${docId}`);
  return response.data;
};

/**
 * Upload tài liệu mới vào knowledge base.
 * Gửi file qua multipart/form-data.
 */
export const uploadRagDocument = async (
  file: File,
  metadata?: string
): Promise<ApiResponse<RagDocument>> => {
  const formData = new FormData();
  formData.append('file', file);

  let url = '/rag/documents';
  if (metadata && metadata.trim()) {
    url += `?doc_metadata=${encodeURIComponent(metadata.trim())}`;
  }

  const response = await apiClient.post(url, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

/**
 * Xóa tài liệu RAG (xóa cả Qdrant vectors + DB record).
 */
export const deleteRagDocument = async (
  docId: string
): Promise<ApiResponse<RagDocumentDeleteData>> => {
  const response = await apiClient.delete(`/rag/documents/${docId}`);
  return response.data;
};

/**
 * Health check: kiểm tra trạng thái Qdrant collection.
 */
export const getRagHealth = async (): Promise<ApiResponse<RagHealthData>> => {
  const response = await apiClient.get('/rag/health');
  return response.data;
};
