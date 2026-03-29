/**
 * Generic API Response type for Admin services
 */
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
}

/**
 * Dashboard Overview Statistics
 * Matches backend DashboardOverviewResponse
 */
export interface DashboardOverview {
  total_users: number;
  new_users_this_month: number;
  growth_rate: number;
  total_images: number;
  analyzed_images: number;
  image_growth_rate: number;
  new_uploads_week: number;
  total_detections: number;
  detection_growth_rate: number;
  severe_detections: number;
  new_detections_week: number;
  model_accuracy: number;
  accuracy_trend: number;
  high_confidence_detections: number;
}

/**
 * Wound Type Distribution Item
 * Matches backend WoundTypeDistributionItem
 */
export interface WoundTypeItem {
  name: string;
  value: number;
  color: string;
  [key: string]: string | number;
}

/**
 * Wound Type Distribution Response
 * Matches backend WoundTypeDistributionResponse
 */
export interface WoundTypeDistributionResponse {
  distribution: WoundTypeItem[];
  total_detections: number;
}

/**
 * Severity Statistics Item
 * Matches backend SeverityStatsItem
 */
export interface SeverityStatsItem {
  name: string;
  value: number;
  color: string;
  [key: string]: string | number;
}

/**
 * Severity Statistics Response
 * Matches backend SeverityStatsResponse
 */
export interface SeverityStatsResponse {
  stats: SeverityStatsItem[];
  total_detections: number;
}

/**
 * System Log Entry
 * Matches backend SystemLogItem
 */
export interface SystemLogItem {
  type: string;
  message: string;
  time: string;
  severity: string;
  timestamp?: string;
}

/**
 * System Logs Response
 * Matches backend SystemLogsResponse
 */
export interface SystemLogsResponse {
  logs: SystemLogItem[];
  total_logs: number;
  unresolved_errors: number;
}

/**
 * Weekly Activity Item
 * Matches backend DailyActivityItem
 */
export interface DailyActivityItem {
  date: string;
  uploads: number;
  analyses: number;
}

/**
 * Weekly Activity Response
 * Matches backend WeeklyActivityResponse
 */
export interface WeeklyActivityResponse {
  daily_stats: DailyActivityItem[];
  total_uploads: number;
  total_analyses: number;
}

/**
 * Severity Statistics Response (updated)
 * Matches backend SeverityStatsResponse
 */
export interface SeverityStatsResponse {
  distribution: Record<string, number>;
  total: number;
}

// ============== Model Management Types ==============

/**
 * Model performance metrics
 */
export interface ModelMetrics {
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  [key: string]: number | undefined;
}

/**
 * AI Model information
 */
export interface AIModel {
  model_id: string;
  model_type: 'detection' | 'classification' | 'segmentation' | 'severity_scoring';
  name: string;
  description?: string;
  current_version?: string;
  is_active: boolean;
  total_versions: number;
  created_at: string;
  updated_at: string;
  created_by?: string;
  metrics?: ModelMetrics;
  version_tag?: string;
  versions?: ModelVersion[];
}

/**
 * Model version information
 */
export interface ModelVersion {
  version_id: string;
  model_id: string;
  version_tag: string;
  version_number: number;
  is_active: boolean;
  is_beta: boolean;
  created_at: string;
  deployed_at?: string;
  deployed_by?: string;
  metrics?: ModelMetrics;
}

/**
 * Model list response
 */
export interface ModelListResponse {
  models: AIModel[];
  active_version?: string;
  total: number;
  filters_applied: any;
}

/**
 * Model detail response
 */
export interface ModelDetailResponse {
  model: AIModel;
  versions: ModelVersion[];
  active_version?: ModelVersion;
  version_history: any[];
}

/**
 * Model upload request
 */
export interface ModelUploadRequest {
  model_type: string;
  version_tag: string;
  description?: string;
  is_beta: boolean;
  metrics?: ModelMetrics;
}

/**
 * Model upload response
 */
export interface ModelUploadResponse {
  success: boolean;
  model_id: string;
  version_id: string;
  version_tag: string;
  file_size_bytes: number;
  file_path: string;
  uploaded_at: string;
  message: string;
}

/**
 * Model activate response
 */
export interface ModelActivateResponse {
  success: boolean;
  active_version: string;
  previous_version?: string;
  activated_at: string;
  model_id: string;
  message: string;
}

/**
 * Model rollback response
 */
export interface ModelRollbackResponse {
  success: boolean;
  previous_version: string;
  rolled_back_version: string;
  rolled_back_at: string;
  model_id: string;
  message: string;
}

/**
 * Model delete response
 */
export interface ModelDeleteResponse {
  success: boolean;
  deleted_version: string;
  deleted_at: string;
  is_permanent: boolean;
  message: string;
}
