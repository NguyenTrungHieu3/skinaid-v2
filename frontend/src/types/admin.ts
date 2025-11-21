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
