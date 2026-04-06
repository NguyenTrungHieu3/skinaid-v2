import apiClient from './api';

// ─── Types ────────────────────────────────────────────────────────────────────
export interface AnswerOption {
  answer_id: string;
  question_id: string;
  answer_text: string;
  triage_level: 'green' | 'yellow' | 'red';
  icon_or_color: string | null;
  order_index: number;
  metadata_tags: Record<string, unknown> | null;
}

export interface Question {
  question_id: string;
  questionnaire_id: string;
  question_text: string;
  order_index: number;
  is_multiple_choice: boolean;
  is_active: boolean;
  answers: AnswerOption[];
}

export interface Questionnaire {
  questionnaire_id: string;
  wound_type: string;
  title: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  questions: Question[];
}

export interface QuestionnaireCreate {
  wound_type: string;
  title: string;
  description?: string;
  is_active?: boolean;
}

export interface QuestionnaireUpdate {
  title?: string;
  description?: string;
  is_active?: boolean;
}

export interface QuestionCreate {
  question_text: string;
  order_index?: number;
  is_multiple_choice?: boolean;
  is_active?: boolean;
  answers?: AnswerCreate[];
}

export interface QuestionUpdate {
  question_text?: string;
  order_index?: number;
  is_multiple_choice?: boolean;
  is_active?: boolean;
}

export interface AnswerCreate {
  answer_text: string;
  triage_level: 'green' | 'yellow' | 'red';
  icon_or_color?: string;
  order_index?: number;
  metadata_tags?: Record<string, unknown>;
}

export interface AnswerUpdate {
  answer_text?: string;
  triage_level?: 'green' | 'yellow' | 'red';
  icon_or_color?: string;
  order_index?: number;
  metadata_tags?: Record<string, unknown>;
}

// ─── API Calls ────────────────────────────────────────────────────────────────
export const getAllQuestionnaires = async (): Promise<Questionnaire[]> => {
  const res = await apiClient.get('/questionnaires/');
  return res.data;
};

export const getQuestionnaire = async (id: string): Promise<Questionnaire> => {
  const res = await apiClient.get(`/questionnaires/${id}`);
  return res.data;
};

export const createQuestionnaire = async (data: QuestionnaireCreate): Promise<Questionnaire> => {
  const res = await apiClient.post('/questionnaires/', data);
  return res.data;
};

export const updateQuestionnaire = async (
  id: string,
  data: QuestionnaireUpdate
): Promise<Questionnaire> => {
  const res = await apiClient.put(`/questionnaires/${id}`, data);
  return res.data;
};

export const activateQuestionnaire = async (id: string): Promise<Questionnaire> => {
  const res = await apiClient.post(`/questionnaires/${id}/activate`);
  return res.data;
};

export const deleteQuestionnaire = async (id: string): Promise<void> => {
  await apiClient.delete(`/questionnaires/${id}`);
};

export const addQuestion = async (
  questionnaireId: string,
  data: QuestionCreate
): Promise<Question> => {
  const res = await apiClient.post(`/questionnaires/${questionnaireId}/questions`, data);
  return res.data;
};

export const updateQuestion = async (
  questionId: string,
  data: QuestionUpdate
): Promise<Question> => {
  const res = await apiClient.put(`/questionnaires/questions/${questionId}`, data);
  return res.data;
};

export const deleteQuestion = async (questionId: string): Promise<void> => {
  await apiClient.delete(`/questionnaires/questions/${questionId}`);
};

export const addAnswer = async (
  questionId: string,
  data: AnswerCreate
): Promise<AnswerOption> => {
  const res = await apiClient.post(`/questionnaires/questions/${questionId}/answers`, data);
  return res.data;
};

export const updateAnswer = async (
  answerId: string,
  data: AnswerUpdate
): Promise<AnswerOption> => {
  const res = await apiClient.put(`/questionnaires/answers/${answerId}`, data);
  return res.data;
};

export const deleteAnswer = async (answerId: string): Promise<void> => {
  await apiClient.delete(`/questionnaires/answers/${answerId}`);
};

// ─── Import ───────────────────────────────────────────────────────────────────

export interface ImportPreview {
  total_rows: number;
  errors: string[];
  preview: Record<string, string>[];
}

export const previewImportFile = async (file: File): Promise<ImportPreview> => {
  const form = new FormData();
  form.append('file', file);
  const res = await apiClient.post('/questionnaires/import/preview', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const importFileToQuestionnaire = async (
  questionnaireId: string,
  file: File
): Promise<Questionnaire> => {
  const form = new FormData();
  form.append('file', file);
  const res = await apiClient.post(`/questionnaires/${questionnaireId}/import`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

// ─── Export ───────────────────────────────────────────────────────────────────

/** Download a Blob as a file. Appends <a> to DOM and delays revokeObjectURL so
 *  browsers (especially Firefox & Safari) have time to initiate the download. */
const _downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  // Delay revoke so the browser has time to start the download
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};

/**
 * When responseType:'blob' is used, axios wraps error responses as Blobs too.
 * This helper reads the Blob as text and extracts the FastAPI `detail` message.
 */
const _parseBlobError = async (err: any): Promise<string> => {
  const blob: Blob | undefined = err?.response?.data;
  if (blob instanceof Blob) {
    try {
      const text = await blob.text();
      const json = JSON.parse(text);
      if (typeof json?.detail === 'string') return json.detail;
      if (typeof json?.detail === 'object') return JSON.stringify(json.detail);
      if (typeof json?.message === 'string') return json.message;
    } catch {
      // blob was not JSON — return raw text (truncated)
      try {
        const text = await blob.text();
        return text.slice(0, 300) || 'Xuất file thất bại';
      } catch { /* ignore */ }
    }
  }
  return (err?.message as string) || 'Xuất file thất bại';
};

export const exportQuestionnairePdf = async (id: string, title: string): Promise<void> => {
  try {
    const res = await apiClient.get(`/questionnaires/${id}/export/pdf`, { responseType: 'blob' });
    _downloadBlob(res.data, `${title}.pdf`);
  } catch (err) {
    throw new Error(await _parseBlobError(err));
  }
};

export const exportQuestionnaireDocx = async (id: string, title: string): Promise<void> => {
  try {
    const res = await apiClient.get(`/questionnaires/${id}/export/docx`, { responseType: 'blob' });
    _downloadBlob(res.data, `${title}.docx`);
  } catch (err) {
    throw new Error(await _parseBlobError(err));
  }
};

/** Export as re-importable CSV (full format: wound_type, title, questions, answers…) */
export const exportQuestionnaireCsv = async (id: string, title: string): Promise<void> => {
  try {
    const res = await apiClient.get(`/questionnaires/${id}/export/csv`, { responseType: 'blob' });
    _downloadBlob(res.data, `${title}_export.csv`);
  } catch (err) {
    throw new Error(await _parseBlobError(err));
  }
};

/** Export as re-importable Excel (full format: wound_type, title, questions, answers…) */
export const exportQuestionnaireExcel = async (id: string, title: string): Promise<void> => {
  try {
    const res = await apiClient.get(`/questionnaires/${id}/export/excel`, { responseType: 'blob' });
    _downloadBlob(res.data, `${title}_export.xlsx`);
  } catch (err) {
    throw new Error(await _parseBlobError(err));
  }
};


export const downloadCsvTemplate = async (): Promise<void> => {
  const res = await apiClient.get('/questionnaires/templates/csv', { responseType: 'blob' });
  _downloadBlob(res.data, 'questionnaire_template.csv');
};

export const downloadExcelTemplate = async (): Promise<void> => {
  const res = await apiClient.get('/questionnaires/templates/excel', { responseType: 'blob' });
  _downloadBlob(res.data, 'questionnaire_template.xlsx');
};

export const downloadFullCsvTemplate = async (): Promise<void> => {
  const res = await apiClient.get('/questionnaires/templates/full-csv', { responseType: 'blob' });
  _downloadBlob(res.data, 'full_questionnaire_template.csv');
};

export const downloadFullExcelTemplate = async (): Promise<void> => {
  const res = await apiClient.get('/questionnaires/templates/full-excel', { responseType: 'blob' });
  _downloadBlob(res.data, 'full_questionnaire_template.xlsx');
};

// ─── Import Full Questionnaire ────────────────────────────────────────────────

export interface FullImportQuestionPreview {
  order: number;
  text: string;
  answers_count: number;
}

export interface FullImportGroupPreview {
  wound_type: string;
  title: string;
  description: string;
  is_active: boolean;
  total_questions: number;
  questions_preview: FullImportQuestionPreview[];
}

export interface FullImportPreview {
  total_questionnaires: number;
  errors: string[];
  preview: FullImportGroupPreview[];
}

export const previewFullImportFile = async (file: File): Promise<FullImportPreview> => {
  const form = new FormData();
  form.append('file', file);
  const res = await apiClient.post('/questionnaires/import/full/preview', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const importFullQuestionnaire = async (
  file: File,
  autoActivate = false
): Promise<{ imported: number; questionnaire_id: string; title: string; wound_type: string; errors: string[] }> => {
  const form = new FormData();
  form.append('file', file);
  const res = await apiClient.post(
    `/questionnaires/import/full?auto_activate=${autoActivate}`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return res.data;
};

export const importBulkQuestionnaires = async (
  file: File
): Promise<{ imported: number; questionnaires: { questionnaire_id: string; title: string; wound_type: string; is_active: boolean }[]; errors: string[] }> => {
  const form = new FormData();
  form.append('file', file);
  const res = await apiClient.post('/questionnaires/import/bulk', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

// ─── Coverage ─────────────────────────────────────────────────────────────────

export interface WoundTypeCoverage {
  wound_type: string;
  total: number;
  has_active: boolean;
  active_title: string | null;
}

export interface CoverageReport {
  coverage: WoundTypeCoverage[];
  total_wound_types: number;
  covered: number;
  uncovered: number;
}

export const getCoverage = async (): Promise<CoverageReport> => {
  const res = await apiClient.get('/questionnaires/coverage');
  return res.data;
};

