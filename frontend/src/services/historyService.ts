import api, { BACKEND_URL } from "./api";
import {
  type ApiSuccessResponse,
} from "../types/responseTypes";
import {
  type ApiHistoryListResponse,
  type ApiWoundAnalysisResponse,
} from "../types/historyTypes";
import {
  type HistoryEvent,
  type CombinedEventDetail,
  type SingleWoundDetail,
} from "../types/appTypes"; // Import kiểu frontend từ appTypes

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
    throw new Error(error.response?.data?.message || "Error loading history");
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
    throw new Error(error.response?.data?.message || "Error loading details");
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
    throw new Error(error.response?.data?.message || "Error deleting analysis");
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
    title: `${new Date(event.created_at).toLocaleDateString(
      "en-US"
    )}`,
    date: event.created_at,
    status: event.total_detections === 0
      ? "No wounds detected"
      : `${event.total_detections} detection(s)`,
    imageUrl: `${BACKEND_URL}${event.image_url}`,
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

      //Lấy sơ cứu Nên làm
      const shouldDoString = (snapshot.dos || [])
        .map((d: string, index: number) => `${index + 1}. ${d}`)
        .join(" ");

      //Lấy sơ cứu Không nên làm
      const shouldNotDoString = (snapshot.donts || [])
        .map((d: string, index: number) => `${index + 1}. ${d}`)
        .join(" ");

      const titleString = (snapshot.title || '')

      const suppliesNeededString = (snapshot.supplies_needed || [])
        .map((s: string, index: number) => `${index + 1}. ${s}`)
        .join(" ");

      return {
        type: wound.wound_type,
        accuracy: wound.confidence_score * 100, // Chuyển 0.95 -> 95
        severity: wound.severity, // Lấy trực tiếp từ 'significant_wounds'
        sub_type: wound.sub_type || '', // Lấy trực tiếp từ 'significant_wounds'
        reliable_source: snapshot.source || {},
        healingTime: snapshot.estimated_healing_time || "",
        firstAid: firstAidString || "",
        shouldDo: shouldDoString || "",
        shouldNotDo: shouldNotDoString || "",
        titleGuide: titleString || "",
        suppliesNeeded: suppliesNeededString || "",
      };
    }
  );

  return {
    id: apiEvent.analysis_id,
    title: `Analysis ${new Date(apiEvent.created_at).toLocaleDateString(
      "en-US"
    )}`,
    date: apiEvent.created_at,
    status: apiEvent.total_detections === 0
      ? "No wounds detected"
      : `${apiEvent.total_detections} detection(s)`,
    imageUrl: `${BACKEND_URL}${apiEvent.image_url}`,
    detail: details,
  };
}
