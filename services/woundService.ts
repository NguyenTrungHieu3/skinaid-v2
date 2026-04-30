// services/woundService.ts
// Tập trung toàn bộ API calls cho FC1: wound analysis & first-aid result

import axiosClient from '../api/axiosClient';
import { getErrorMessage } from './utils';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface AnalyzeResponse {
  analysis_id: string;
  image_url: string;
  file_name: string;
  total_detections: number;
  ai_model_version: string;
  analyzed_at: string;
}

export interface FirstAidSnapshot {
  title: string;
  steps: string[];
  dos: string[];
  donts: string[];
  supplies_needed: string[];
  estimated_healing_time: string;
  source: string | null;
}

export interface SignificantWound {
  detection_id: string;
  wound_type: string;          // 'abrasion' | 'bruise' | 'burn' | 'acne' | 'psoriasis' | 'fungal'
  severity: string;            // 'mild' | 'moderate' | 'severe'
  sub_type: string | null;
  confidence_score: number;    // 0–1
  bounding_box: { x: number; y: number; width: number; height: number };
  detection_index: number;
  firstaid_guide_id: string;
  firstaid_snapshot: FirstAidSnapshot; // fallback hoàn chỉnh khi LLM không hoạt động
}

export interface AnalysisDetailResponse {
  analysis_id: string;
  image_url: string;
  file_name: string;
  total_detections: number;
  significant_wounds: SignificantWound[];
  analyzed_at: string;
  user_responses?: {
    response_id: string;
    question_id: string;
    answer_id: string;
    created_at: string;
  }[];
}

export interface HistoryEvent {
  analysis_id: string;
  user_id: string;
  guest_session_id: string | null;
  image_url: string;
  file_name: string;
  total_detections: number;
  processing_time_ms: number;
  analyzed_at: string;
  created_at: string;
}

export interface AnalysisHistoryResponse {
  total: number;
  limit: number;
  offset: number;
  events: HistoryEvent[];
}

export interface QuestionnaireAnswer {
  answer_id: string;
  answer_text: string;
  triage_level: 'green' | 'yellow' | 'red';
  order_index: number;
  question_id: string;
}

export interface QuestionnaireQuestion {
  question_id: string;
  question_text: string;
  order_index: number;
  is_multiple_choice: boolean;
  answers: QuestionnaireAnswer[];
}

export interface ResolvedQuestionnaire {
  wound_type: string;
  subtype: string | null;
  severity: string;
  representative_detection_id: string;
  detection_count: number;
  questionnaire: {
    questionnaire_id: string;
    wound_type: string;
    title: string;
    description: string;
    questions: QuestionnaireQuestion[]; // số câu là động, tùy wound_type
  };
}

export interface SubmitDetection {
  detection_id: string;
  wound_type: string;
  subtype: string | null;
  severity: string;
  confidence: number;
}

export interface SubmitAnswer {
  question_id: string;
  answer_ids: string[];
}

export interface SynthesisResult {
  wound_type: string;
  subtype: string | null;
  severity: string;
  source: 'llm' | 'db' | 'fallback';
  guidance: string;
  structured_guidance: {
    title: string;
    steps: string[];
    dos: string[];
    donts: string[];
    supplies_needed: string[];
    estimated_healing_time: string;
  } | null;
  validated: boolean;
  error: string | null;
}

export interface SubmitResponse {
  aggregated_triage: 'green' | 'yellow' | 'red';
  selections: Array<{
    question_id: string;
    answer_ids: string[];
    triage_levels: string[];
  }>;
  syntheses: SynthesisResult[];
}

// ─── Mapping helpers ──────────────────────────────────────────────────────────

export const WOUND_TYPE_MAP: Record<string, string> = {
  abrasion: 'tray',
  bruise: 'bam',
  burn: 'bong',
  acne: 'mun-trung-ca',
  psoriasis: 'vay-nen',
  fungal: 'nam-da',
};

export const WOUND_LABEL_MAP: Record<string, string> = {
  abrasion: 'Trầy xước',
  bruise: 'Bầm tím',
  burn: 'Bỏng',
  acne: 'Mụn trứng cá',
  psoriasis: 'Vảy nến',
  fungal: 'Nấm da',
};

export function mapWoundTypeId(apiType: string): string {
  return WOUND_TYPE_MAP[apiType] ?? apiType;
}

export function mapWoundLabel(apiType: string): string {
  return WOUND_LABEL_MAP[apiType] ?? apiType;
}

export function mapSeverityColor(severity: string): string {
  if (severity === 'severe') return '#EF4444';   // đỏ
  if (severity === 'moderate') return '#F59E0B'; // vàng
  return '#10B981';                               // xanh (mild)
}

export function mapSeverityLabel(severity: string): string {
  if (severity === 'severe') return 'Nặng';
  if (severity === 'moderate') return 'Trung bình';
  return 'Nhẹ';
}

// ─── API calls ────────────────────────────────────────────────────────────────

/**
 * [API-1] Gửi ảnh để AI phân tích nhận diện vết thương.
 * Dùng multipart/form-data với field tên "file".
 */
export async function analyzeWoundImage(imageUri: string): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append('file', {
    uri: imageUri,
    name: `wound_${Date.now()}.jpg`,
    type: 'image/jpeg',
  } as unknown as Blob);

  const response = await axiosClient.post('/ai/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data.data as AnalyzeResponse;
}

/**
 * [API-2] Lấy chi tiết kết quả phân tích.
 * Response chứa firstaid_snapshot trong mỗi SignificantWound —
 * đây là nguồn dữ liệu sơ cứu dùng khi LLM fallback.
 */
export async function getAnalysisDetail(analysisId: string): Promise<AnalysisDetailResponse> {
  const response = await axiosClient.get(`/ai/analysis/${analysisId}`);
  return response.data.data as AnalysisDetailResponse;
}

/**
 * Lấy lịch sử phân tích (chỉ có metadata cơ bản, thiếu chi tiết vết thương)
 */
export async function getAnalysisHistory(limit = 20, offset = 0): Promise<AnalysisHistoryResponse> {
  const response = await axiosClient.get(`/ai/history`, {
    params: { limit, offset }
  });
  return response.data.data as AnalysisHistoryResponse;
}

/**
 * [API-3] Resolve bộ câu hỏi tương ứng với các vết thương người dùng đã chọn.
 * Dedupe theo (wound_type, subtype) — mỗi cặp duy nhất 1 bộ câu hỏi.
 * Số câu hỏi trả về là động (tùy wound_type), không hardcode.
 */
export async function resolveQuestionnaires(
  detections: SubmitDetection[]
): Promise<ResolvedQuestionnaire[]> {
  const response = await axiosClient.post('/wound-responses/resolve-questionnaires', {
    detections,
  });
  return response.data.data.questionnaires as ResolvedQuestionnaire[];
}

/**
 * [API-4] Submit câu trả lời + tổng hợp kết quả sơ cứu qua LLM.
 * forward_to_synthesis=true  → LLM tổng hợp (nếu LLM available).
 * forward_to_synthesis=false → chỉ validate answers, không gọi LLM.
 */
export async function submitWoundResponses(payload: {
  analysis_id: string;
  user_description?: string;
  detections: SubmitDetection[];
  answers: SubmitAnswer[];
  forward_to_synthesis: boolean;
}): Promise<SubmitResponse> {
  // LLM synthesis có thể mất 30-60 giây, dùng timeout riêng 90s thay vì default 10s
  const response = await axiosClient.post('/wound-responses/submit', payload, {
    timeout: 90000,
  });
  return response.data.data as SubmitResponse;
}
