/**
 * Tương ứng với Pydantic schema 'WoundDetectionSummary'
 */
export interface ApiWoundDetectionSummary {
  wound_type: string;
  severity: string;
  sub_type: string | null;
  confidence_score: number;
  bounding_box: Record<string, any>;
  firstaid_snapshot: Record<string, any> | null;

  // Các trường @computed_field từ Pydantic
  confidence_percentage: number;
  meets_threshold: boolean;
}

/**
 * Tương ứng với Pydantic schema 'WoundAnalysisResponse'
 */
export interface ApiWoundAnalysisResponse {
  analysis_id: string;
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
  user_id: string | null;
  image_url: string;
  file_name: string;
  file_size: number;
  ai_model_version: string;
  total_detections: number;
  processing_time_ms: number;
  analyzed_at: string | null; // ISO date string

  // Các trường @computed_field từ Pydantic
  is_successful_analysis: boolean;
  has_multiple_wounds: boolean;
  is_wound_detected: boolean;
  processing_time_seconds: number | null;
  average_confidence: number;
  meets_accuracy_threshold: boolean;
  is_guest_analysis: boolean;

  significant_wounds: ApiWoundDetectionSummary[];
  wound_guides: Record<string, any> | null;
}

/**
 * Kiểu dữ liệu mà API GET /ai/history trả về trong 'data'
 * (Dựa trên `SuccessResponse[Dict[str, Any]]`)
 */
export interface ApiHistoryListResponse {
  total: number;
  events: ApiWoundAnalysisResponse[];
  // Thêm các thống kê khác nếu có
}
