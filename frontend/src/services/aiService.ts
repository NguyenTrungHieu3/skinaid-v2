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
  steps: string[];
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

// --- LLM Synthesis types ---

export interface StructuredGuidance {
  title: string;
  steps: string[];
  dos: string[];
  donts: string[];
  supplies_needed: string[];
  estimated_healing_time: string | null;
}

export interface LLMSynthesizeRequest {
  analysis_id?: string;        // UUID — nếu có, BE sẽ persist guidance vào Detection.firstaid_snapshot
  wound_type: string;
  severity: string;
  sub_type?: string | null;
  user_description?: string;  // optional — không cần khi chưa có questionnaire
  top_k_rag?: number;
}

export interface LLMSynthesizeResponse {
  guidance: string;
  source: "llm" | "db";
  validated: boolean;
  db_guide_available: boolean;
  rag_chunks_used: number;
  model_version: string;
  tokens_used: number;
  processing_time_ms: number;
  confidence_score: number | null;
  structured_guidance: StructuredGuidance | null;
}

// --- 2. HÀM GỌI API ---

/**
 * Global abort controller for in-flight AI requests.
 * Call abortActiveAnalysis() on logout to cancel pending /ai/analyze calls (TC-LO-09).
 */
let activeAnalysisController: AbortController | null = null;

export const abortActiveAnalysis = () => {
  if (activeAnalysisController) {
    activeAnalysisController.abort();
    activeAnalysisController = null;
  }
};

/**
 * 1. POST /ai/analyze
 * Gửi file ảnh lên để bắt đầu phân tích.
 */
export const analyzeImage = (formData: FormData, signal?: AbortSignal) => {
  activeAnalysisController = new AbortController();
  const finalSignal = signal ?? activeAnalysisController.signal;
  return apiClient.post<SuccessResponse<AnalysisPostResponse>>(
    "/ai/analyze",
    formData,
    { signal: finalSignal }
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

/**
 * 3. POST /llm/synthesize
 * Tổng hợp hướng dẫn sơ cứu từ AI result — có thể gọi ngay mà không cần questionnaire.
 */
export const synthesizeGuidance = (payload: LLMSynthesizeRequest) => {
  return apiClient.post<SuccessResponse<LLMSynthesizeResponse>>(
    "/llm/synthesize",
    payload
  );
};
