import apiClient from "./api";
// Giả sử bạn có file types chung
import type { SuccessResponse } from "../types";

// --- 1. ĐỊNH NGHĨA TYPES (DỰA TRÊN JSON CỦA BẠN) ---

// Type cho Response của POST /ai/analyze
export interface AnalysisPostResponse {
  analysis_id: string;
  created_at: string;
  updated_at: string;
}

// Types chi tiết cho Response của GET /ai/analysis/{id}
export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface FirstAidSnapshot {
  title: string;
  description: string;
  steps: string[];
  warnings: string[];
  dos: string[];
  donts: string[];
  supplies_needed: string[];
  estimated_healing_time: string;
}

export interface SignificantWound {
  wound_type: string;
  severity: string;
  sub_type: string | null;
  confidence_score: number;
  bounding_box: BoundingBox;
  firstaid_snapshot: FirstAidSnapshot;
}

export interface AnalysisGetResponse {
  analysis_id: string;
  image_url: string;
  file_name: string;
  total_detections: number;
  processing_time_ms: number;
  analyzed_at: string;
  significant_wounds: SignificantWound[];
  // (Thêm các trường khác từ JSON nếu bạn cần)
}

// --- 2. HÀM GỌI API ---

/**
 * 1. POST /ai/analyze
 * Gửi file ảnh lên để bắt đầu phân tích.
 */
export const analyzeImage = (formData: FormData) => {
  // return apiClient.post<SuccessResponse<AnalysisPostResponse>>(
  //   "/ai/analyze", // (Giả sử apiClient có baseURL là /api/v1)
  //   formData,
  //   {
  //     headers: {
  //       // Axios cần header này khi gửi FormData
  //       "Content-Type": "multipart/form-data",
  //     },
  //   }
  // );

  return apiClient.post<SuccessResponse<AnalysisPostResponse>>(
    "/ai/analyze", // (Giả sử apiClient có baseURL là /api/v1)
    formData
    // Không cần khối config { headers: ... } ở đây nữa
  );
};

/**
 * 2. GET /ai/analysis/{id}
 * Lấy kết quả chi tiết của một phân tích đã hoàn thành.
 */
export const getAnalysisResult = (analysisId: string) => {
  return apiClient.get<SuccessResponse<AnalysisGetResponse>>(
    `/ai/analysis/${analysisId}`
  );
};
