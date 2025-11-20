import api from "./api"; // Giả định import từ file api.ts của bạn
import {
  type ApiSuccessResponse,
  type ApiErrorResponse,
} from "../types/responseTypes";
import {
  type ApiHistoryListResponse,
  type ApiWoundAnalysisResponse,
} from "../types/historyTypes";
import {
  type HistoryEvent,
  type CombinedEventDetail,
  type SingleWoundDetail,
} from "../DUMMY_DATA"; // Import kiểu frontend

// --- CÁC HÀM GỌI API ---

/**
 * Lấy lịch sử phân tích (GET /ai/history)
 */
export const getHistory = async (
  limit: number = 20,
  offset: number = 0
): Promise<ApiHistoryListResponse> => {
  try {
    const response = await api.get<ApiSuccessResponse<ApiHistoryListResponse>>(
      `/ai/history?limit=${limit}&offset=${offset}`
    );
    return response.data.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.message || "Không thể tải lịch sử");
  }
};

/**
 * Lấy chi tiết một phân tích (GET /ai/analysis/{analysis_id})
 */
export const getAnalysisDetail = async (
  analysisId: string
): Promise<ApiWoundAnalysisResponse> => {
  try {
    const response = await api.get<
      ApiSuccessResponse<ApiWoundAnalysisResponse>
    >(`/ai/analysis/${analysisId}`);
    return response.data.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.message || "Không thể tải chi tiết");
  }
};

/**
 * Xóa một phân tích (DELETE /ai/analysis/{analysis_id})
 */
export const deleteAnalysis = async (
  analysisId: string
): Promise<{ message: string }> => {
  try {
    const response = await api.delete<ApiSuccessResponse<{ message: string }>>(
      `/ai/analysis/${analysisId}`
    );
    return response.data.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.message || "Không thể xóa phân tích");
  }
};

// --- CÁC HÀM BIẾN ĐỔI (TRANSFORMERS) ---

/**
 * Biến đổi API response (list) thành data cho Timeline (HistoryEvent)
 */
export function transformApiHistoryToTimeline(
  apiData: ApiWoundAnalysisResponse[]
): HistoryEvent[] {
  return apiData.map((event) => ({
    id: event.analysis_id,
    title: `Phân tích ${new Date(event.created_at).toLocaleDateString(
      "vi-VN"
    )}`,
    date: event.created_at,
    status: `${event.total_detections} detection(s)`,
    imageUrl: `http://localhost:8000${event.image_url}`,
  }));
}

/**
 * Biến đổi API response (detail) thành data cho HistoryDetail (CombinedEventDetail)
 */
export function transformApiDetailToCombinedEvent(
  apiEvent: ApiWoundAnalysisResponse
): CombinedEventDetail {
  // Biến đổi significant_wounds (API) thành detail (Frontend)
  const details: SingleWoundDetail[] = apiEvent.significant_wounds.map(
    (wound) => {
      // Pydantic schema của bạn có 'firstaid_snapshot'
      const snapshot = wound.firstaid_snapshot || {};

      // Tách chuỗi firstAid (nếu có)
      const firstAidString = (snapshot.steps || [])
        .map((step: string, index: number) => `${index + 1}. ${step}`)
        .join(" ");

      return {
        type: wound.wound_type,
        accuracy: wound.confidence_score * 100, // Chuyển 0.95 -> 95
        severity: wound.severity, // Lấy trực tiếp từ 'significant_wounds'
        description: snapshot.description || "Không có mô tả.",
        healingTime: snapshot.estimated_healing_time || "Chưa có dữ liệu",
        firstAid: firstAidString || "Không có gợi ý sơ cứu.",
      };
    }
  );

  return {
    id: apiEvent.analysis_id,
    title: `Phân tích ${new Date(apiEvent.created_at).toLocaleDateString(
      "vi-VN"
    )}`,
    date: apiEvent.created_at,
    status: `${apiEvent.total_detections} detection(s)`,
    imageUrl: `http://localhost:8000${apiEvent.image_url}`,
    detail: details,
  };
}
