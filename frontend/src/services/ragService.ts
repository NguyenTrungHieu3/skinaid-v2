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
  const raw = response.data;

  // Backend returns DocumentListResponse trực tiếp ({total, skip, limit, items}),
  // không bọc trong {success, data}. Normalize tại đây để đồng bộ với
  // uploadRagDocument / deleteRagDocument.
  if (raw && Array.isArray(raw.items)) {
    return {
      success: true,
      message: 'OK',
      data: {
        items: raw.items,
        total: raw.total ?? 0,
        skip: raw.skip ?? 0,
        limit: raw.limit ?? 0,
      },
    };
  }
  return raw;
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

  // Backend expects doc_metadata as a Form field (not query string)
  if (metadata && metadata.trim()) {
    formData.append('doc_metadata', metadata.trim());
  }

  const response = await apiClient.post('/rag/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  // Backend returns DocumentResponse directly (not wrapped), normalize it
  const raw = response.data;
  if (raw && raw.rag_document_id) {
    return { success: true, message: 'Upload thành công', data: raw };
  }
  return raw;
};

/**
 * Xóa tài liệu RAG (xóa cả Qdrant vectors + DB record).
 */
export const deleteRagDocument = async (
  docId: string
): Promise<ApiResponse<RagDocumentDeleteData>> => {
  const response = await apiClient.delete(`/rag/documents/${docId}`);
  const raw = response.data;
  // Backend returns DocumentDeleteResponse directly, normalize it
  if (raw && raw.rag_document_id) {
    return {
      success: true,
      message: 'Xóa thành công',
      data: {
        rag_document_id: raw.rag_document_id,
        file_name: raw.file_name ?? '',
        vectors_deleted: raw.deleted_points ?? 0,
        message: 'Xóa thành công',
      },
    };
  }
  return raw;
};

/**
 * Health check: kiểm tra trạng thái Qdrant collection.
 */
export const getRagHealth = async (): Promise<ApiResponse<RagHealthData>> => {
  const response = await apiClient.get('/rag/health');
  return response.data;
};
