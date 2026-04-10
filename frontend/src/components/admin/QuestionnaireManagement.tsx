import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  GripVertical,
  Edit2,
  Trash2,
  PlusCircle,
  ChevronDown,
  Plus,
  FileQuestion,
  CheckCircle2,
  XCircle,
  ClipboardList,
  Loader2,
  AlertCircle,
  AlertTriangle,
  X,
  Save,
  Upload,
  Download,
  FileSpreadsheet,
  Zap,
  Files,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useToast } from '../../contexts/ToastContext';
import StatCard from './shared/StatCard';
import styles from './QuestionnaireManagement.module.css';
import {
  getAllQuestionnaires,
  createQuestionnaire,
  updateQuestionnaire,
  activateQuestionnaire,
  deleteQuestionnaire,
  addQuestion,
  updateQuestion,
  deleteQuestion,
  addAnswer,
  updateAnswer,
  deleteAnswer,
  previewImportFile,
  importFileToQuestionnaire,
  exportQuestionnairePdf,
  exportQuestionnaireDocx,
  exportQuestionnaireCsv,
  exportQuestionnaireExcel,
  downloadCsvTemplate,
  downloadExcelTemplate,
  downloadFullCsvTemplate,
  downloadFullExcelTemplate,
  previewFullImportFile,
  importBulkMultipleFiles,
  exportBulkQuestionnaires,
  getCoverage,
  type Questionnaire,
  type Question,
  type AnswerOption,
  type ImportPreview,
  type FullImportPreview,
  type FullImportGroupPreview,
  type BulkFilesResult,
  type CoverageReport,
} from '../../services/questionnaireService';

// ─── Constants ────────────────────────────────────────────────────────────────
// Label map for wound types - dùng cho form và display
const WOUND_TYPE_LABEL: Record<string, string> = {
  abrasion:   'Trầy xước (Abrasion)',
  bruise:     'Bầm tím (Bruise)',
  burn:       'Bỏng (Burn)',
  cut:        'Vết cắt (Cut)',
  acne:       'Mụn trứng cá (Acne)',
  fungal:     'Nấm da (Fungal)',
  psoriasis:  'Vảy nến (Psoriasis)',
  laceration: 'Vết rách (Laceration)',
  rash:       'Phát ban (Rash)',
  normal:     'Bình thường (Normal)',
};

// Canonical list dùng trong form Create (đồng bộ với backend VALID_WOUND_TYPES)
const WOUND_TYPES_FORM = [
  { value: 'abrasion',   label: WOUND_TYPE_LABEL.abrasion },
  { value: 'bruise',     label: WOUND_TYPE_LABEL.bruise },
  { value: 'burn',       label: WOUND_TYPE_LABEL.burn },
  { value: 'cut',        label: WOUND_TYPE_LABEL.cut },
  { value: 'acne',       label: WOUND_TYPE_LABEL.acne },
  { value: 'fungal',     label: WOUND_TYPE_LABEL.fungal },
  { value: 'psoriasis',  label: WOUND_TYPE_LABEL.psoriasis },
  { value: 'laceration', label: WOUND_TYPE_LABEL.laceration },
  { value: 'rash',       label: WOUND_TYPE_LABEL.rash },
  { value: 'normal',     label: WOUND_TYPE_LABEL.normal },
];

const TRIAGE_CONFIG = {
  green:  { label: 'Nhẹ',  badgeClass: styles.badgeGreen },
  yellow: { label: 'Vừa',  badgeClass: styles.badgeYellow },
  red:    { label: 'Nặng', badgeClass: styles.badgeRed },
};

const ANSWER_MAX_CHARS = 120; // Mobile: ~2 lines

// ─── Modal helpers ────────────────────────────────────────────────────────────
type ModalType =
  | 'createQuestionnaire'
  | 'editQuestionnaire'
  | 'deleteQuestionnaire'
  | 'createQuestion'
  | 'editQuestion'
  | 'deleteQuestion'
  | 'createAnswer'
  | 'editAnswer'
  | 'deleteAnswer'
  | 'import'
  | 'importUnified'
  | 'exportBulk'
  | null;

export default function QuestionnaireManagement() {
  const { t } = useTranslation();
  const { success, error: toastError } = useToast();

  // ─── Data state ────────────────────────────────────────────────────────────
  const [questionnaires, setQuestionnaires] = useState<Questionnaire[]>([]);
  const [loading, setLoading] = useState(true);
  const [serverError, setServerError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [expandedQuestions, setExpandedQuestions] = useState<Set<string>>(new Set());
  const [submitting, setSubmitting] = useState(false);
  const [filterWoundType, setFilterWoundType] = useState<string>('');
  const [listPage, setListPage] = useState(1);
  const LIST_PAGE_SIZE = 10;
  // Import state (add to existing questionnaire)
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importPreview, setImportPreview] = useState<ImportPreview | null>(null);
  const [importPreviewing, setImportPreviewing] = useState(false);
  const [importTargetId, setImportTargetId] = useState<string | null>(null);
  // Unified import state (multi-file with preview)
  const [bulkFiles, setBulkFiles] = useState<File[]>([]);
  const [bulkFilesAutoActivate, setBulkFilesAutoActivate] = useState(false);
  const [bulkFilesResult, setBulkFilesResult] = useState<BulkFilesResult | null>(null);
  const [bulkFilesPreviews, setBulkFilesPreviews] = useState<Map<string, { preview: FullImportGroupPreview[]; errors: string[] }>>(new Map());
  const [bulkFilesPreviewing, setBulkFilesPreviewing] = useState(false);
  const bulkFileInputRef = useRef<HTMLInputElement>(null);
  // Coverage banner
  const [coverage, setCoverage] = useState<CoverageReport | null>(null);
  // Export dropdown
  const [exportDropdownOpen, setExportDropdownOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const exportRef = useRef<HTMLDivElement>(null);
  // Bulk export state
  const [exportSelectedIds, setExportSelectedIds] = useState<Set<string>>(new Set());
  const [exportFormat, setExportFormat] = useState<'csv' | 'excel' | 'docx' | 'pdf'>('excel');

  // ─── Modal state ───────────────────────────────────────────────────────────
  const [modal, setModal] = useState<ModalType>(null);
  const [modalContext, setModalContext] = useState<
    Questionnaire | Question | AnswerOption | null
  >(null);

  // ─── Form state ───────────────────────────────────────────────────────────
  const [qForm, setQForm] = useState({ wound_type: 'abrasion', title: '', description: '', is_active: false });
  const [queForm, setQueForm] = useState({ question_text: '', is_multiple_choice: false });
  const [ansForm, setAnsForm] = useState({
    answer_text: '',
    triage_level: 'green' as 'green' | 'yellow' | 'red',
  });
  const [answerParentQuestionId, setAnswerParentQuestionId] = useState<string | null>(null);

  // ─── Derived ───────────────────────────────────────────────────────────────
  const selected = questionnaires.find((q) => q.questionnaire_id === selectedId) ?? null;
  const totalActive = questionnaires.filter((q) => q.is_active).length;
  const totalDraft = questionnaires.filter((q) => !q.is_active).length;

  // Extract unique wound types from loaded data for filter dropdown
  const availableWoundTypes = Array.from(new Set(questionnaires.map((q) => q.wound_type))).sort();

  // Filtered list for left panel
  const filteredQuestionnaires = filterWoundType
    ? questionnaires.filter((q) => q.wound_type === filterWoundType)
    : questionnaires;

  // Pagination for left panel list
  const totalListPages = Math.ceil(filteredQuestionnaires.length / LIST_PAGE_SIZE);
  const paginatedQuestionnaires = filteredQuestionnaires.slice(
    (listPage - 1) * LIST_PAGE_SIZE,
    listPage * LIST_PAGE_SIZE
  );

  // Reset page when filter changes
  useEffect(() => {
    setListPage(1);
  }, [filterWoundType]);

  // ─── Load ──────────────────────────────────────────────────────────────────
  const fetchAll = useCallback(async () => {
    try {
      setLoading(true);
      setServerError(null);
      const [data, cov] = await Promise.all([
        getAllQuestionnaires(),
        getCoverage().catch(() => null),
      ]);
      setQuestionnaires(data);
      setCoverage(cov);
      // Auto-select first if none selected
      if (!selectedId && data.length > 0) {
        setSelectedId(data[0].questionnaire_id);
      }
    } catch (err: any) {
      setServerError(err?.response?.data?.detail ?? 'Không thể tải dữ liệu');
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => { fetchAll(); }, []);

  // ─── Accordion toggle ──────────────────────────────────────────────────────
  const toggleQuestion = (id: string) => {
    setExpandedQuestions((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  // ─── Open modals ───────────────────────────────────────────────────────────
  const openCreateQuestionnaire = () => {
    setQForm({ wound_type: 'abrasion', title: '', description: '', is_active: false });
    setModal('createQuestionnaire');
  };

  const openEditQuestionnaire = (q: Questionnaire) => {
    setQForm({ wound_type: q.wound_type, title: q.title, description: q.description ?? '', is_active: q.is_active });
    setModalContext(q);
    setModal('editQuestionnaire');
  };

  const openDeleteQuestionnaire = (q: Questionnaire) => { setModalContext(q); setModal('deleteQuestionnaire'); };

  const openCreateQuestion = () => {
    setQueForm({ question_text: '', is_multiple_choice: false });
    setModal('createQuestion');
  };

  const openEditQuestion = (q: Question) => {
    setQueForm({ question_text: q.question_text, is_multiple_choice: q.is_multiple_choice });
    setModalContext(q);
    setModal('editQuestion');
  };

  const openDeleteQuestion = (q: Question) => { setModalContext(q); setModal('deleteQuestion'); };

  const openCreateAnswer = (questionId: string) => {
    setAnsForm({ answer_text: '', triage_level: 'green' });
    setAnswerParentQuestionId(questionId);
    setModal('createAnswer');
  };

  const openEditAnswer = (a: AnswerOption) => {
    setAnsForm({ answer_text: a.answer_text, triage_level: a.triage_level });
    setModalContext(a);
    setModal('editAnswer');
  };

  const openDeleteAnswer = (a: AnswerOption) => { setModalContext(a); setModal('deleteAnswer'); };

  const openImport = (targetId: string) => {
    setImportTargetId(targetId);
    setImportFile(null);
    setImportPreview(null);
    setModal('import');
  };

  const closeModal = () => {
    setModal(null);
    setModalContext(null);
    setAnswerParentQuestionId(null);
    setImportFile(null);
    setImportPreview(null);
    setImportTargetId(null);
  };

  // ─── Activate handler (1 active per wound_type) ──────────────────────────
  const handleActivate = async (q: Questionnaire) => {
    if (q.is_active) return;
    try {
      await activateQuestionnaire(q.questionnaire_id);
      success(`Đã kích hoạt bộ "${q.title}". Các bộ khác cùng loại đã chuyển sang Nháp.`);
      fetchAll();
    } catch {
      toastError('Kích hoạt thất bại');
    }
  };

  // ─── Toggle status ─────────────────────────────────────────────────────────
  const handleToggleStatus = async () => {
    if (!selected) return;
    try {
      if (!selected.is_active) {
        await activateQuestionnaire(selected.questionnaire_id);
        success('Đã kích hoạt bộ câu hỏi. Các bộ khác cùng loại đã chuyển sang Nháp.');
      } else {
        await updateQuestionnaire(selected.questionnaire_id, { is_active: false });
        success('Đã chuyển sang Nháp');
      }
      fetchAll();
    } catch {
      toastError('Không thể cập nhật trạng thái');
    }
  };

  // ─── Export ────────────────────────────────────────────────────────────────
  const handleExport = async (format: 'pdf' | 'docx' | 'csv' | 'excel') => {
    if (!selected) return;
    try {
      setExporting(true);
      setExportDropdownOpen(false);
      if (format === 'pdf') await exportQuestionnairePdf(selected.questionnaire_id, selected.title);
      else if (format === 'docx') await exportQuestionnaireDocx(selected.questionnaire_id, selected.title);
      else if (format === 'csv') await exportQuestionnaireCsv(selected.questionnaire_id, selected.title);
      else if (format === 'excel') await exportQuestionnaireExcel(selected.questionnaire_id, selected.title);
      success(`Đã xuất ${format.toUpperCase()} thành công!`);
    } catch (err: any) {
      // Service functions now throw Error with parsed blob message
      const msg: string = err?.message || 'Xuất file thất bại';
      toastError(msg);
    } finally {
      setExporting(false);
    }
  };

  // ─── Bulk Export ─────────────────────────────────────────────────────
  const openExportBulk = () => {
    setExportSelectedIds(new Set());
    setExportFormat('excel');
    setModal('exportBulk');
  };

  const toggleExportId = (id: string) => {
    setExportSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleAllExport = () => {
    if (exportSelectedIds.size === questionnaires.length) {
      setExportSelectedIds(new Set());
    } else {
      setExportSelectedIds(new Set(questionnaires.map((q) => q.questionnaire_id)));
    }
  };

  const handleBulkExport = async () => {
    if (exportSelectedIds.size === 0) return;
    try {
      setExporting(true);
      await exportBulkQuestionnaires(Array.from(exportSelectedIds), exportFormat);
      success(`Đã xuất ${exportSelectedIds.size} bộ câu hỏi thành công!`);
    } catch (err: any) {
      toastError(err?.message ?? 'Xuất file thất bại');
    } finally {
      setExporting(false);
    }
  };

  // ─── Import ────────────────────────────────────────────────────────────────
  const handleImportFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImportFile(file);
    setImportPreview(null);
    try {
      setImportPreviewing(true);
      const preview = await previewImportFile(file);
      setImportPreview(preview);
    } catch (err: any) {
      toastError(err?.response?.data?.detail ?? 'Không thể đọc file');
    } finally {
      setImportPreviewing(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!importTargetId || !importFile) return;
    try {
      setSubmitting(true);
      await importFileToQuestionnaire(importTargetId, importFile);
      success('Đã import câu hỏi thành công!');
      closeModal();
      fetchAll();
    } catch (err: any) {
      toastError(err?.response?.data?.detail ?? 'Import thất bại');
    } finally {
      setSubmitting(false);
    }
  };

  // ─── Unified Import handlers (multi-file with preview) ─────────────────
  const resetUnifiedImport = () => {
    setBulkFiles([]);
    setBulkFilesResult(null);
    setBulkFilesPreviews(new Map());
    setBulkFilesAutoActivate(false);
    setBulkFilesPreviewing(false);
  };

  const previewFiles = async (files: File[]) => {
    setBulkFilesPreviewing(true);
    const newPreviews = new Map(bulkFilesPreviews);
    for (const file of files) {
      if (newPreviews.has(file.name)) continue;
      try {
        const result = await previewFullImportFile(file);
        newPreviews.set(file.name, { preview: result.preview, errors: result.errors });
      } catch {
        newPreviews.set(file.name, { preview: [], errors: [`Không thể đọc file ${file.name}`] });
      }
    }
    setBulkFilesPreviews(newPreviews);
    setBulkFilesPreviewing(false);
  };

  const handleBulkFilesSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files ?? []);
    if (selected.length === 0) return;
    const existingNames = new Set(bulkFiles.map((f) => f.name));
    const newFiles = selected.filter((f) => !existingNames.has(f.name));
    if (newFiles.length > 0) {
      setBulkFiles((prev) => [...prev, ...newFiles]);
      previewFiles(newFiles);
    }
    e.target.value = '';
  };

  const handleBulkFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const dropped = Array.from(e.dataTransfer.files).filter(
      (f) => f.name.endsWith('.csv') || f.name.endsWith('.xlsx') || f.name.endsWith('.xls')
    );
    if (dropped.length === 0) return;
    const existingNames = new Set(bulkFiles.map((f) => f.name));
    const newFiles = dropped.filter((f) => !existingNames.has(f.name));
    if (newFiles.length > 0) {
      setBulkFiles((prev) => [...prev, ...newFiles]);
      previewFiles(newFiles);
    }
  };

  const removeBulkFile = (index: number) => {
    const removed = bulkFiles[index];
    setBulkFiles((prev) => prev.filter((_, i) => i !== index));
    if (removed) {
      setBulkFilesPreviews((prev) => {
        const next = new Map(prev);
        next.delete(removed.name);
        return next;
      });
    }
  };

  // Derived: total questionnaires found across all previewed files
  const totalPreviewedQuestionnaires = Array.from(bulkFilesPreviews.values()).reduce(
    (sum, p) => sum + p.preview.length, 0
  );
  const allPreviewErrors = Array.from(bulkFilesPreviews.entries()).flatMap(
    ([fname, p]) => p.errors.map((e) => `[${fname}] ${e}`)
  );

  const handleConfirmBulkFiles = async () => {
    if (bulkFiles.length === 0) return;
    try {
      setSubmitting(true);
      const result = await importBulkMultipleFiles(bulkFiles, bulkFilesAutoActivate);
      setBulkFilesResult(result);
      success(`Đã import ${result.imported} bộ câu hỏi từ ${bulkFiles.length} file!`);
      fetchAll();
    } catch (err: any) {
      toastError(err?.response?.data?.detail?.message ?? err?.response?.data?.detail ?? 'Import thất bại');
    } finally {
      setSubmitting(false);
    }
  };

  // ─── Questionnaire CRUD ────────────────────────────────────────────────────
  const handleCreateQuestionnaire = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!qForm.title.trim()) return;
    try {
      setSubmitting(true);
      const created = await createQuestionnaire({
        wound_type: qForm.wound_type,
        title: qForm.title.trim(),
        description: qForm.description.trim() || undefined,
        is_active: qForm.is_active,
      });
      success('Đã tạo bộ câu hỏi mới');
      closeModal();
      await fetchAll();
      setSelectedId(created.questionnaire_id);
    } catch (err: any) {
      toastError(err?.response?.data?.detail ?? 'Tạo thất bại');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditQuestionnaire = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!(modalContext as Questionnaire)?.questionnaire_id) return;
    try {
      setSubmitting(true);
      await updateQuestionnaire((modalContext as Questionnaire).questionnaire_id, {
        title: qForm.title.trim(),
        description: qForm.description.trim() || undefined,
        is_active: qForm.is_active,
      });
      success('Đã cập nhật bộ câu hỏi');
      closeModal();
      fetchAll();
    } catch {
      toastError('Cập nhật thất bại');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteQuestionnaire = async () => {
    if (!(modalContext as Questionnaire)?.questionnaire_id) return;
    try {
      setSubmitting(true);
      await deleteQuestionnaire((modalContext as Questionnaire).questionnaire_id);
      success('Đã xóa bộ câu hỏi');
      closeModal();
      setSelectedId(null);
      fetchAll();
    } catch {
      toastError('Xóa thất bại');
    } finally {
      setSubmitting(false);
    }
  };

  // ─── Question CRUD ─────────────────────────────────────────────────────────
  const handleCreateQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected || !queForm.question_text.trim()) return;
    try {
      setSubmitting(true);
      const nextOrder = (selected.questions?.length ?? 0) + 1;
      await addQuestion(selected.questionnaire_id, {
        question_text: queForm.question_text.trim(),
        is_multiple_choice: queForm.is_multiple_choice,
        order_index: nextOrder,
      });
      success('Đã thêm câu hỏi');
      closeModal();
      fetchAll();
    } catch {
      toastError('Thêm câu hỏi thất bại');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = modalContext as Question;
    if (!q?.question_id) return;
    try {
      setSubmitting(true);
      await updateQuestion(q.question_id, {
        question_text: queForm.question_text.trim(),
        is_multiple_choice: queForm.is_multiple_choice,
      });
      success('Đã cập nhật câu hỏi');
      closeModal();
      fetchAll();
    } catch {
      toastError('Cập nhật câu hỏi thất bại');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteQuestion = async () => {
    const q = modalContext as Question;
    if (!q?.question_id) return;
    try {
      setSubmitting(true);
      await deleteQuestion(q.question_id);
      success('Đã xóa câu hỏi');
      closeModal();
      fetchAll();
    } catch {
      toastError('Xóa câu hỏi thất bại');
    } finally {
      setSubmitting(false);
    }
  };

  // ─── Answer CRUD ───────────────────────────────────────────────────────────
  const handleCreateAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answerParentQuestionId || !ansForm.answer_text.trim()) return;
    try {
      setSubmitting(true);
      await addAnswer(answerParentQuestionId, {
        answer_text: ansForm.answer_text.trim(),
        triage_level: ansForm.triage_level,
      });
      success('Đã thêm đáp án');
      closeModal();
      fetchAll();
    } catch {
      toastError('Thêm đáp án thất bại');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    const a = modalContext as AnswerOption;
    if (!a?.answer_id) return;
    try {
      setSubmitting(true);
      await updateAnswer(a.answer_id, {
        answer_text: ansForm.answer_text.trim(),
        triage_level: ansForm.triage_level,
      });
      success('Đã cập nhật đáp án');
      closeModal();
      fetchAll();
    } catch {
      toastError('Cập nhật đáp án thất bại');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteAnswer = async () => {
    const a = modalContext as AnswerOption;
    if (!a?.answer_id) return;
    try {
      setSubmitting(true);
      await deleteAnswer(a.answer_id);
      success('Đã xóa đáp án');
      closeModal();
      fetchAll();
    } catch {
      toastError('Xóa đáp án thất bại');
    } finally {
      setSubmitting(false);
    }
  };

  // ─── Loading / Error ───────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className={styles.loadingState}>
        <div className={styles.loadingSpinner} />
        <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Đang tải dữ liệu...</p>
      </div>
    );
  }

  if (serverError) {
    return (
      <div className={styles.errorState}>
        <AlertCircle size={32} />
        <p>{serverError}</p>
        <button className={styles.btnOutline} onClick={fetchAll} style={{ marginTop: '1rem' }}>Thử lại</button>
      </div>
    );
  }

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <div className={styles.questionnaireManagementPage}>
      <title>{t('title.admin_questionnaire')}</title>
      {/* Header */}
      <div className={styles.adminPageHeader}>
        <div className={styles.adminPageTitle}>
          <h1>{t('admin.questionnaires.title')}</h1>
          <p>{t('admin.questionnaires.subtitle')}</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            className={styles.btnOutline}
            style={{ fontSize: '0.8rem', padding: '0.5rem 0.875rem' }}
            onClick={() => { resetUnifiedImport(); setModal('importUnified'); }}
            title="Import bộ câu hỏi từ file CSV/Excel"
          >
            <Upload size={15} /> Import bộ câu hỏi
          </button>
          <button
            className={styles.btnOutline}
            style={{ fontSize: '0.8rem', padding: '0.5rem 0.875rem' }}
            onClick={openExportBulk}
            title="Xuất nhiều bộ câu hỏi ra file"
          >
            <Download size={15} /> Export bộ câu hỏi
          </button>
          <button className={styles.adminBtnPrimary} onClick={openCreateQuestionnaire}>
            <PlusCircle size={18} />
            {t('admin.questionnaires.create_new')}
          </button>
        </div>
      </div>


      {/* Stats */}
      <div className={styles.statsGrid}>
        <StatCard
          icon={ClipboardList}
          value={questionnaires.length}
          label={t('admin.questionnaires.total')}
          color="primary"
        />
        <StatCard
          icon={CheckCircle2}
          value={totalActive}
          label={t('admin.questionnaires.active')}
          color="green"
        />
        <StatCard
          icon={XCircle}
          value={totalDraft}
          label={t('admin.questionnaires.draft')}
          color="default"
        />
      </div>

      {/* Coverage Banner – show when there are uncovered wound types */}
      {coverage && coverage.uncovered > 0 && (
        <div className={styles.coverageBanner}>
          <div className={styles.coverageBannerIcon}><AlertTriangle size={16} /></div>
          <div className={styles.coverageBannerText}>
            <strong>{coverage.uncovered} loại vết thương</strong> chưa có bộ câu hỏi active: 
            {coverage.coverage
              .filter(c => !c.has_active)
              .map(c => <span key={c.wound_type} className={styles.coverageUncoveredBadge}>{WOUND_TYPE_LABEL[c.wound_type] ?? c.wound_type}</span>)
            }
          </div>
          <button
            className={styles.coverageBannerAction}
            onClick={() => { resetUnifiedImport(); setModal('importUnified'); }}
          >
            Import nhanh
          </button>
        </div>
      )}

      {/* Main Layout */}
      <div className={styles.mainLayout}>
        {/* ─── Left Panel ─── */}
        <div className={styles.leftPanel}>
          <div className={styles.listCard}>
            {/* Filter bar */}
            <div className={styles.listFilterBar}>
              <label className={styles.filterLabel}>LOẠI VẾT THƯƠNG</label>
              <select
                className={styles.listFilterSelect}
                value={filterWoundType}
                onChange={(e) => {
                  setFilterWoundType(e.target.value);
                  // Nếu item đang chọn bị filter out thì bỏ selection
                  if (e.target.value && selected && selected.wound_type !== e.target.value) {
                    setSelectedId(null);
                  }
                }}
              >
                <option value="">Tất cả loại vết thương ({questionnaires.length})</option>
                {availableWoundTypes.map((wt) => (
                  <option key={wt} value={wt}>
                    {WOUND_TYPE_LABEL[wt] ?? wt} ({questionnaires.filter(q => q.wound_type === wt).length})
                  </option>
                ))}
              </select>
            </div>
            <div className={styles.listCardHeader}>
              {filterWoundType
                ? `Kết quả lọc: ${filteredQuestionnaires.length} bộ câu hỏi`
                : `Danh sách (${questionnaires.length})`}
              {filterWoundType && (
                <button
                  className={styles.filterClearBtn}
                  onClick={() => setFilterWoundType('')}
                  title="Xóa bộ lọc"
                >
                  ✕
                </button>
              )}
            </div>
            {paginatedQuestionnaires.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8', fontSize: '0.875rem' }}>
                {filterWoundType ? `Không có bộ câu hỏi nào cho loại vết thương này` : 'Chưa có bộ câu hỏi nào'}
              </div>
            ) : (
              paginatedQuestionnaires.map((q) => (
                <div
                  key={q.questionnaire_id}
                  role="button"
                  tabIndex={0}
                  className={`${styles.questionnaireListItem} ${selectedId === q.questionnaire_id ? styles.active : ''}`}
                  onClick={() => setSelectedId(q.questionnaire_id)}
                  onKeyDown={(e) => e.key === 'Enter' && setSelectedId(q.questionnaire_id)}
                >
                  <div className={styles.listItemContent}>
                    <p className={styles.listItemTitle}>{q.title}</p>
                    <p className={styles.listItemMeta}>{WOUND_TYPE_LABEL[q.wound_type] ?? q.wound_type}</p>
                  </div>
                  <div className={styles.listItemRight}>
                    <span className={`${styles.badge} ${q.is_active ? styles.badgeActive : styles.badgeDraft}`}>
                      {q.is_active ? 'Active' : 'Draft'}
                    </span>
                    {!q.is_active && (
                      <button
                        className={styles.listItemActivateBtn}
                        onClick={(e) => { e.stopPropagation(); handleActivate(q); }}
                        title="Kích hoạt bộ câu hỏi này"
                      >
                        <Zap size={11} />
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
            {/* Pagination cho danh sách */}
            {filteredQuestionnaires.length > LIST_PAGE_SIZE && (
              <div style={{ padding: '0.75rem 1rem', borderTop: '1px solid #e2e8f0' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
                    Hiển thị {(listPage - 1) * LIST_PAGE_SIZE + 1}-{Math.min(listPage * LIST_PAGE_SIZE, filteredQuestionnaires.length)} / {filteredQuestionnaires.length}
                  </span>
                  <div style={{ display: 'flex', gap: '0.25rem' }}>
                    <button
                      disabled={listPage === 1}
                      onClick={() => setListPage(p => Math.max(1, p - 1))}
                      style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem', border: '1px solid #e2e8f0', borderRadius: '0.375rem', background: 'white', cursor: listPage === 1 ? 'not-allowed' : 'pointer', opacity: listPage === 1 ? 0.4 : 1, color: '#475569' }}
                    >
                      ‹ Trước
                    </button>
                    {Array.from({ length: totalListPages }, (_, i) => i + 1).map(p => (
                      <button
                        key={p}
                        onClick={() => setListPage(p)}
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem', border: '1px solid', borderColor: p === listPage ? '#17805f' : '#e2e8f0', borderRadius: '0.375rem', background: p === listPage ? '#17805f' : 'white', color: p === listPage ? 'white' : '#475569', cursor: 'pointer', fontWeight: p === listPage ? 600 : 400, minWidth: '1.75rem' }}
                      >
                        {p}
                      </button>
                    ))}
                    <button
                      disabled={listPage === totalListPages}
                      onClick={() => setListPage(p => Math.min(totalListPages, p + 1))}
                      style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem', border: '1px solid #e2e8f0', borderRadius: '0.375rem', background: 'white', cursor: listPage === totalListPages ? 'not-allowed' : 'pointer', opacity: listPage === totalListPages ? 0.4 : 1, color: '#475569' }}
                    >
                      Tiếp ›
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ─── Right Panel ─── */}
        {selected ? (
          <div className={styles.rightPanel}>
            {/* Panel Header */}
            <div className={styles.rightPanelHeader}>
              <div className={styles.rightPanelTitle}>
                <h2>{selected.title}</h2>
            <p>{WOUND_TYPE_LABEL[selected.wound_type] ?? selected.wound_type}</p>
              </div>
              <div className={styles.rightPanelActions}>
                <button
                  className={`${styles.toggleStatusBtn} ${selected.is_active ? styles.toggleStatusBtnActive : styles.toggleStatusBtnDraft}`}
                  onClick={handleToggleStatus}
                >
                  {selected.is_active ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                  {selected.is_active ? 'Hoạt động' : 'Nháp'}
                </button>

                {/* Export dropdown */}
                <div className={styles.exportDropdownWrap} ref={exportRef}>
                  <button
                    className={`${styles.iconBtn} ${styles.iconBtnExport}`}
                    onClick={() => setExportDropdownOpen(p => !p)}
                    title="Xuất bộ câu hỏi"
                    disabled={exporting}
                  >
                    {exporting ? <Loader2 size={15} className={styles.spinIcon} /> : <Download size={15} />}
                  </button>
                  {exportDropdownOpen && (
                    <div className={styles.exportDropdown}>
                      <div className={styles.exportDropdownSection}>📄 Xuất tài liệu</div>
                      <button onClick={() => handleExport('pdf')}>
                        <FileSpreadsheet size={14} /> Xuất PDF
                      </button>
                      <button onClick={() => handleExport('docx')}>
                        <FileSpreadsheet size={14} /> Xuất Word (.docx)
                      </button>
                      <div className={styles.exportDropdownSep} />
                      <div className={styles.exportDropdownSection}>♻️ Xuất để re-import</div>
                      <button onClick={() => handleExport('csv')}>
                        <Download size={14} /> Xuất CSV (re-import)
                      </button>
                      <button onClick={() => handleExport('excel')}>
                        <Download size={14} /> Xuất Excel (re-import)
                      </button>
                      <div className={styles.exportDropdownSep} />
                      <div className={styles.exportDropdownSection}>📋 Tải file mẫu</div>
                      <button onClick={() => { setExportDropdownOpen(false); downloadCsvTemplate(); }}>
                        <Download size={14} /> Mẫu CSV (thêm câu hỏi)
                      </button>
                      <button onClick={() => { setExportDropdownOpen(false); downloadExcelTemplate(); }}>
                        <Download size={14} /> Mẫu Excel (thêm câu hỏi)
                      </button>
                    </div>
                  )}
                </div>

                {/* Import button */}
                <button
                  className={`${styles.iconBtn} ${styles.iconBtnImport}`}
                  onClick={() => openImport(selected.questionnaire_id)}
                  title="Import câu hỏi từ file"
                >
                  <Upload size={15} />
                </button>

                <button className={styles.iconBtn} onClick={() => openEditQuestionnaire(selected)} title="Sửa">
                  <Edit2 size={15} className={styles.iconBtnEdit} />
                </button>
                <button className={styles.iconBtn} onClick={() => openDeleteQuestionnaire(selected)} title="Xóa">
                  <Trash2 size={15} className={styles.iconBtnDelete} />
                </button>
              </div>
            </div>

            {/* Panel Body – Questions */}
            <div className={styles.rightPanelBody}>
              <div className={styles.questionsHeader}>
                <span className={styles.questionsTitle}>
                  <FileQuestion size={16} />
                  Danh sách câu hỏi ({selected.questions?.length ?? 0})
                </span>
                <button className={`${styles.btnOutline} ${styles.btnOutlineSm}`} onClick={openCreateQuestion}>
                  <Plus size={14} /> Thêm câu hỏi
                </button>
              </div>

              {!selected.questions || selected.questions.length === 0 ? (
                <div className={styles.emptyState}>
                  <FileQuestion size={36} color="#cbd5e1" />
                  <p>Chưa có câu hỏi nào. Thêm câu hỏi đầu tiên để bắt đầu.</p>
                  <button className={styles.btnOutline} onClick={openCreateQuestion}>
                    <Plus size={14} /> Thêm câu hỏi
                  </button>
                </div>
              ) : (
                <div className={styles.questionsList}>
                  {[...selected.questions]
                    .sort((a, b) => a.order_index - b.order_index)
                    .map((q, idx) => {
                      const isExpanded = expandedQuestions.has(q.question_id);
                      return (
                        <div key={q.question_id} className={styles.questionCard}>
                          {/* Question header */}
                          <div className={styles.questionCardHeader} onClick={() => toggleQuestion(q.question_id)} role="button" tabIndex={0} onKeyDown={(e) => e.key === 'Enter' && toggleQuestion(q.question_id)}>
                            <GripVertical size={16} className={styles.dragHandle} />
                            <div className={styles.questionIndex}>{idx + 1}</div>
                            <span className={styles.questionText}>{q.question_text}</span>
                            <span className={styles.questionTypeBadge}>
                              {q.is_multiple_choice ? 'Multi' : 'Single'}
                            </span>
                            <div className={styles.questionActions} onClick={(e) => e.stopPropagation()}>
                              <button className={styles.iconBtn} onClick={() => openEditQuestion(q)} title="Sửa">
                                <Edit2 size={14} className={styles.iconBtnEdit} />
                              </button>
                              <button className={styles.iconBtn} onClick={() => openDeleteQuestion(q)} title="Xóa">
                                <Trash2 size={14} className={styles.iconBtnDelete} />
                              </button>
                            </div>
                            <ChevronDown size={16} className={`${styles.chevronIcon} ${isExpanded ? styles.expanded : ''}`} />
                          </div>

                          {/* Answers section */}
                          {isExpanded && (
                            <div className={styles.answersSection}>
                              <div className={styles.answersHeader}>
                                <span className={styles.answersTitle}>Đáp án ({q.answers?.length ?? 0})</span>
                                <button className={`${styles.btnOutline} ${styles.btnOutlineSm}`} onClick={() => openCreateAnswer(q.question_id)}>
                                  <Plus size={12} /> Thêm
                                </button>
                              </div>

                              <div className={styles.answersList}>
                                {(!q.answers || q.answers.length === 0) ? (
                                  <p style={{ color: '#94a3b8', fontSize: '0.8rem', textAlign: 'center', padding: '0.75rem' }}>
                                    Chưa có đáp án nào
                                  </p>
                                ) : (
                                  [...q.answers]
                                    .sort((a, b) => a.order_index - b.order_index)
                                    .map((ans) => {
                                      const triage = TRIAGE_CONFIG[ans.triage_level] ?? TRIAGE_CONFIG.green;
                                      return (
                                        <div key={ans.answer_id} className={styles.answerRow}>
                                          <span className={styles.answerText}>{ans.answer_text}</span>
                                          <span className={`${styles.badge} ${triage.badgeClass}`}>{triage.label}</span>
                                          <div className={styles.answerRowActions}>
                                            <button className={styles.iconBtn} onClick={() => openEditAnswer(ans)} title="Sửa">
                                              <Edit2 size={13} className={styles.iconBtnEdit} />
                                            </button>
                                            <button className={styles.iconBtn} onClick={() => openDeleteAnswer(ans)} title="Xóa">
                                              <Trash2 size={13} className={styles.iconBtnDelete} />
                                            </button>
                                          </div>
                                        </div>
                                      );
                                    })
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}

                  {/* Add more question */}
                  <button className={styles.btnDashed} onClick={openCreateQuestion}>
                    <PlusCircle size={16} /> Thêm câu hỏi mới
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className={styles.noSelectionState}>
            <ClipboardList size={40} color="#e2e8f0" />
            <p>Chọn một bộ câu hỏi ở bên trái để xem chi tiết</p>
          </div>
        )}
      </div>

      {/* ─── MODALS ─── */}

      {/* Create Questionnaire */}
      {modal === 'createQuestionnaire' && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>Tạo Bộ Câu Hỏi Mới</h2>
              <button className={styles.modalClose} onClick={closeModal}><X size={16} /></button>
            </div>
            <form onSubmit={handleCreateQuestionnaire}>
              <div className={styles.modalBody}>
                <div className={styles.formGroup}>
                  <label>Loại vết thương *</label>
                  <select value={qForm.wound_type} onChange={(e) => setQForm({ ...qForm, wound_type: e.target.value })}>
                    {WOUND_TYPES_FORM.map((w) => <option key={w.value} value={w.value}>{w.label}</option>)}
                  </select>
                </div>
                <div className={styles.formGroup}>
                  <label>Tiêu đề bộ câu hỏi *</label>
                  <input type="text" value={qForm.title} onChange={(e) => setQForm({ ...qForm, title: e.target.value })} placeholder="VD: Bộ câu hỏi đánh giá Bỏng" required />
                </div>
                <div className={styles.formGroup}>
                  <label>Mô tả (tùy chọn)</label>
                  <textarea value={qForm.description} onChange={(e) => setQForm({ ...qForm, description: e.target.value })} placeholder="Mô tả ngắn về mục đích bộ câu hỏi..." />
                </div>
                <label className={styles.checkboxRow}>
                  <input type="checkbox" checked={qForm.is_active} onChange={(e) => setQForm({ ...qForm, is_active: e.target.checked })} />
                  Kích hoạt ngay (Active)
                </label>
              </div>
              <div className={styles.modalActions}>
                <button type="button" className={styles.btnSecondary} onClick={closeModal}>Hủy</button>
                <button type="submit" className={styles.btnSubmit} disabled={submitting}>
                  {submitting ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                  Tạo bộ câu hỏi
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Questionnaire */}
      {modal === 'editQuestionnaire' && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>Chỉnh sửa Bộ Câu Hỏi</h2>
              <button className={styles.modalClose} onClick={closeModal}><X size={16} /></button>
            </div>
            <form onSubmit={handleEditQuestionnaire}>
              <div className={styles.modalBody}>
                <div className={styles.formGroup}>
                  <label>Tiêu đề *</label>
                  <input type="text" value={qForm.title} onChange={(e) => setQForm({ ...qForm, title: e.target.value })} required />
                </div>
                <div className={styles.formGroup}>
                  <label>Mô tả</label>
                  <textarea value={qForm.description} onChange={(e) => setQForm({ ...qForm, description: e.target.value })} />
                </div>
                <label className={styles.checkboxRow}>
                  <input type="checkbox" checked={qForm.is_active} onChange={(e) => setQForm({ ...qForm, is_active: e.target.checked })} />
                  Kích hoạt (Active)
                </label>
              </div>
              <div className={styles.modalActions}>
                <button type="button" className={styles.btnSecondary} onClick={closeModal}>Hủy</button>
                <button type="submit" className={styles.btnSubmit} disabled={submitting}>
                  {submitting ? <Loader2 size={14} /> : <Save size={14} />} Lưu thay đổi
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Questionnaire */}
      {modal === 'deleteQuestionnaire' && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>Xóa Bộ Câu Hỏi</h2>
              <button className={styles.modalClose} onClick={closeModal}><X size={16} /></button>
            </div>
            <div className={styles.modalBody}>
              <p style={{ color: '#475569', fontSize: '0.9rem' }}>
                Bạn có chắc muốn xóa bộ câu hỏi <strong>"{(modalContext as Questionnaire)?.title}"</strong>?
                Hành động này sẽ xóa toàn bộ câu hỏi và đáp án bên trong và <strong>không thể hoàn tác</strong>.
              </p>
            </div>
            <div className={styles.modalActions}>
              <button className={styles.btnSecondary} onClick={closeModal}>Hủy</button>
              <button className={styles.btnDanger} onClick={handleDeleteQuestionnaire} disabled={submitting}>
                {submitting ? <Loader2 size={14} /> : <Trash2 size={14} />} Xóa vĩnh viễn
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Question */}
      {modal === 'createQuestion' && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>Thêm Câu Hỏi</h2>
              <button className={styles.modalClose} onClick={closeModal}><X size={16} /></button>
            </div>
            <form onSubmit={handleCreateQuestion}>
              <div className={styles.modalBody}>
                <div className={styles.formGroup}>
                  <label>Nội dung câu hỏi *</label>
                  <textarea
                    value={queForm.question_text}
                    onChange={(e) => setQueForm({ ...queForm, question_text: e.target.value })}
                    placeholder="VD: Vết bỏng có diện tích như thế nào?"
                    rows={3}
                    required
                  />
                </div>
                <label className={styles.checkboxRow}>
                  <input type="checkbox" checked={queForm.is_multiple_choice} onChange={(e) => setQueForm({ ...queForm, is_multiple_choice: e.target.checked })} />
                  Cho phép chọn nhiều đáp án (Multi-choice)
                </label>
              </div>
              <div className={styles.modalActions}>
                <button type="button" className={styles.btnSecondary} onClick={closeModal}>Hủy</button>
                <button type="submit" className={styles.btnSubmit} disabled={submitting}>
                  {submitting ? <Loader2 size={14} /> : <Save size={14} />} Thêm câu hỏi
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Question */}
      {modal === 'editQuestion' && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>Sửa Câu Hỏi</h2>
              <button className={styles.modalClose} onClick={closeModal}><X size={16} /></button>
            </div>
            <form onSubmit={handleEditQuestion}>
              <div className={styles.modalBody}>
                <div className={styles.formGroup}>
                  <label>Nội dung câu hỏi *</label>
                  <textarea value={queForm.question_text} onChange={(e) => setQueForm({ ...queForm, question_text: e.target.value })} rows={3} required />
                </div>
                <label className={styles.checkboxRow}>
                  <input type="checkbox" checked={queForm.is_multiple_choice} onChange={(e) => setQueForm({ ...queForm, is_multiple_choice: e.target.checked })} />
                  Cho phép chọn nhiều đáp án
                </label>
              </div>
              <div className={styles.modalActions}>
                <button type="button" className={styles.btnSecondary} onClick={closeModal}>Hủy</button>
                <button type="submit" className={styles.btnSubmit} disabled={submitting}>
                  {submitting ? <Loader2 size={14} /> : <Save size={14} />} Lưu
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Question */}
      {modal === 'deleteQuestion' && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>Xóa Câu Hỏi</h2>
              <button className={styles.modalClose} onClick={closeModal}><X size={16} /></button>
            </div>
            <div className={styles.modalBody}>
              <p style={{ color: '#475569', fontSize: '0.9rem' }}>
                Bạn có chắc muốn xóa câu hỏi này? Toàn bộ đáp án của câu hỏi cũng sẽ bị xóa.
              </p>
            </div>
            <div className={styles.modalActions}>
              <button className={styles.btnSecondary} onClick={closeModal}>Hủy</button>
              <button className={styles.btnDanger} onClick={handleDeleteQuestion} disabled={submitting}>
                {submitting ? <Loader2 size={14} /> : <Trash2 size={14} />} Xóa
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Answer */}
      {modal === 'createAnswer' && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>Thêm Đáp Án</h2>
              <button className={styles.modalClose} onClick={closeModal}><X size={16} /></button>
            </div>
            <form onSubmit={handleCreateAnswer}>
              <div className={styles.modalBody}>
                <div className={styles.formGroup}>
                  <label>Nội dung đáp án * (tối đa {ANSWER_MAX_CHARS} ký tự)</label>
                  <textarea
                    value={ansForm.answer_text}
                    onChange={(e) => setAnsForm({ ...ansForm, answer_text: e.target.value })}
                    placeholder="VD: Bỏng nhỏ, diện tích dưới 10cm²"
                    rows={2}
                    maxLength={ANSWER_MAX_CHARS}
                    required
                  />
                  <p className={`${styles.charWarning} ${ansForm.answer_text.length > ANSWER_MAX_CHARS * 0.9 ? styles.charWarningWarn : styles.charWarningOk}`}>
                    {ansForm.answer_text.length}/{ANSWER_MAX_CHARS}
                  </p>
                </div>
                <div className={styles.formGroup}>
                  <label>Mức độ Triage *</label>
                  <select value={ansForm.triage_level} onChange={(e) => setAnsForm({ ...ansForm, triage_level: e.target.value as 'green' | 'yellow' | 'red' })}>
                    <option value="green">🟢 Nhẹ (Green)</option>
                    <option value="yellow">🟡 Vừa (Yellow)</option>
                    <option value="red">🔴 Nặng (Red)</option>
                  </select>
                </div>
              </div>
              <div className={styles.modalActions}>
                <button type="button" className={styles.btnSecondary} onClick={closeModal}>Hủy</button>
                <button type="submit" className={styles.btnSubmit} disabled={submitting}>
                  {submitting ? <Loader2 size={14} /> : <Save size={14} />} Thêm đáp án
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Answer */}
      {modal === 'editAnswer' && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>Sửa Đáp Án</h2>
              <button className={styles.modalClose} onClick={closeModal}><X size={16} /></button>
            </div>
            <form onSubmit={handleEditAnswer}>
              <div className={styles.modalBody}>
                <div className={styles.formGroup}>
                  <label>Nội dung đáp án * (tối đa {ANSWER_MAX_CHARS} ký tự)</label>
                  <textarea
                    value={ansForm.answer_text}
                    onChange={(e) => setAnsForm({ ...ansForm, answer_text: e.target.value })}
                    rows={2}
                    maxLength={ANSWER_MAX_CHARS}
                    required
                  />
                  <p className={`${styles.charWarning} ${ansForm.answer_text.length > ANSWER_MAX_CHARS * 0.9 ? styles.charWarningWarn : styles.charWarningOk}`}>
                    {ansForm.answer_text.length}/{ANSWER_MAX_CHARS}
                  </p>
                </div>
                <div className={styles.formGroup}>
                  <label>Mức độ Triage *</label>
                  <select value={ansForm.triage_level} onChange={(e) => setAnsForm({ ...ansForm, triage_level: e.target.value as 'green' | 'yellow' | 'red' })}>
                    <option value="green">🟢 Nhẹ (Green)</option>
                    <option value="yellow">🟡 Vừa (Yellow)</option>
                    <option value="red">🔴 Nặng (Red)</option>
                  </select>
                </div>
              </div>
              <div className={styles.modalActions}>
                <button type="button" className={styles.btnSecondary} onClick={closeModal}>Hủy</button>
                <button type="submit" className={styles.btnSubmit} disabled={submitting}>
                  {submitting ? <Loader2 size={14} /> : <Save size={14} />} Lưu
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Answer */}
      {modal === 'deleteAnswer' && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>Xóa Đáp Án</h2>
              <button className={styles.modalClose} onClick={closeModal}><X size={16} /></button>
            </div>
            <div className={styles.modalBody}>
              <p style={{ color: '#475569', fontSize: '0.9rem' }}>
                Bạn có chắc muốn xóa đáp án <strong>"{(modalContext as AnswerOption)?.answer_text}"</strong>?
              </p>
            </div>
            <div className={styles.modalActions}>
              <button className={styles.btnSecondary} onClick={closeModal}>Hủy</button>
              <button className={styles.btnDanger} onClick={handleDeleteAnswer} disabled={submitting}>
                {submitting ? <Loader2 size={14} /> : <Trash2 size={14} />} Xóa
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import Modal */}
      {modal === 'import' && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className={styles.modalHeader}>
              <h2><Upload size={16} /> Import Câu Hỏi Từ File</h2>
              <button className={styles.modalClose} onClick={closeModal}><X size={16} /></button>
            </div>
            <div className={styles.modalBody}>
              <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '0.75rem' }}>
                Hỗ trợ file <strong>CSV (.csv)</strong> và <strong>Excel (.xlsx, .xls)</strong>.
                Các câu hỏi sế được thêm vào bộ câu hỏi hiện tại.
              </p>
              <div className={styles.importTemplateLinks}>
                <button type="button" className={styles.btnOutline} onClick={() => downloadCsvTemplate()} style={{ fontSize: '0.8rem' }}>
                  <Download size={13} /> Tải mẫu CSV
                </button>
                <button type="button" className={styles.btnOutline} onClick={() => downloadExcelTemplate()} style={{ fontSize: '0.8rem' }}>
                  <Download size={13} /> Tải mẫu Excel
                </button>
              </div>
              <div className={styles.formGroup} style={{ marginTop: '1rem' }}>
                <label>Chọn file *</label>
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleImportFileChange}
                  className={styles.fileInput}
                />
              </div>
              {importPreviewing && (
                <div style={{ textAlign: 'center', padding: '1rem', color: '#64748b' }}>
                  <Loader2 size={20} className={styles.spinIcon} /> Đang đọc file...
                </div>
              )}
              {importPreview && (
                <div className={styles.importPreviewBox}>
                  <div className={styles.importPreviewHeader}>
                    <span>Tiền xem: <strong>{importPreview.total_rows}</strong> dòng</span>
                    {importPreview.errors.length > 0 && (
                      <span className={styles.importWarning}>⚠️ {importPreview.errors.length} cảnh báo</span>
                    )}
                  </div>
                  {importPreview.errors.length > 0 && (
                    <ul className={styles.importErrorList}>
                      {importPreview.errors.slice(0, 5).map((e, i) => <li key={i}>{e}</li>)}
                    </ul>
                  )}
                  <div className={styles.importPreviewTable}>
                    <table>
                      <thead>
                        <tr>
                          <th>#</th><th>Câu hỏi</th><th>Đáp án</th><th>Triage</th>
                        </tr>
                      </thead>
                      <tbody>
                        {importPreview.preview.slice(0, 10).map((row, i) => (
                          <tr key={i}>
                            <td>{row.question_order}</td>
                            <td>{row.question_text}</td>
                            <td>{row.answer_text}</td>
                            <td>
                              <span className={`${styles.badge} ${
                                row.triage_level === 'green' ? styles.badgeGreen
                                : row.triage_level === 'yellow' ? styles.badgeYellow
                                : styles.badgeRed
                              }`}>{row.triage_level}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {importPreview.preview.length > 10 && (
                      <p style={{ fontSize: '0.75rem', color: '#94a3b8', padding: '0.5rem' }}>
                        ... và {importPreview.preview.length - 10} dòng khác
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
            <div className={styles.modalActions}>
              <button type="button" className={styles.btnSecondary} onClick={closeModal}>Hủy</button>
              <button
                className={styles.btnSubmit}
                onClick={handleConfirmImport}
                disabled={submitting || !importFile || !importPreview || importPreview.total_rows === 0}
              >
                {submitting ? <Loader2 size={14} className={styles.spinIcon} /> : <Upload size={14} />}
                Xác nhận import ({importPreview?.total_rows ?? 0} dòng)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Unified Import Modal ─── */}
      {modal === 'importUnified' && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px' }}>
            <div className={styles.modalHeader}>
              <h2><Upload size={16} /> Import Bộ Câu Hỏi</h2>
              <button className={styles.modalClose} onClick={closeModal}><X size={16} /></button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.fullImportModeInfo}>
                <strong>Import bộ câu hỏi từ file</strong> — Chọn một hoặc nhiều file CSV/Excel.
                Mỗi file có thể chứa một hoặc nhiều bộ câu hỏi. Hệ thống sẽ tự động nhận diện.
              </div>

              {/* Templates */}
              <div className={styles.importTemplateLinks} style={{ marginBottom: '1rem' }}>
                <button type="button" className={styles.btnOutline} onClick={() => downloadFullCsvTemplate()} style={{ fontSize: '0.78rem' }}>
                  <Download size={13} /> Tải mẫu CSV
                </button>
                <button type="button" className={styles.btnOutline} onClick={() => downloadFullExcelTemplate()} style={{ fontSize: '0.78rem' }}>
                  <Download size={13} /> Tải mẫu Excel
                </button>
                <span className={styles.importFormatHint}>Định dạng: wound_type, title, description, is_active, question_order, question_text, is_multiple_choice, answer_text, triage_level</span>
              </div>

              {/* Drag & Drop zone */}
              {!bulkFilesResult && (
                <>
                  <div
                    className={styles.bulkDropZone}
                    onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add(styles.bulkDropZoneActive); }}
                    onDragLeave={(e) => { e.currentTarget.classList.remove(styles.bulkDropZoneActive); }}
                    onDrop={(e) => { e.currentTarget.classList.remove(styles.bulkDropZoneActive); handleBulkFileDrop(e); }}
                    onClick={() => bulkFileInputRef.current?.click()}
                  >
                    <Upload size={28} strokeWidth={1.5} />
                    <p><strong>Kéo thả file vào đây</strong> hoặc nhấn để chọn</p>
                    <span>Hỗ trợ .csv, .xlsx, .xls — có thể chọn một hoặc nhiều file</span>
                    <input
                      ref={bulkFileInputRef}
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      multiple
                      onChange={handleBulkFilesSelect}
                      style={{ display: 'none' }}
                    />
                  </div>

                  {/* File list */}
                  {bulkFiles.length > 0 && (
                    <div className={styles.bulkFileList}>
                      <div className={styles.bulkFileListHeader}>
                        <span><FileSpreadsheet size={14} /> {bulkFiles.length} file đã chọn</span>
                        <button
                          type="button"
                          className={styles.filterClearBtn}
                          onClick={() => { setBulkFiles([]); setBulkFilesPreviews(new Map()); }}
                          title="Xóa tất cả"
                        >
                          Xóa tất cả
                        </button>
                      </div>
                      {bulkFiles.map((f, i) => (
                        <div key={`${f.name}-${i}`} className={styles.bulkFileItem}>
                          <FileSpreadsheet size={16} className={styles.bulkFileIcon} />
                          <div className={styles.bulkFileInfo}>
                            <span className={styles.bulkFileName}>{f.name}</span>
                            <span className={styles.bulkFileSize}>
                              {(f.size / 1024).toFixed(1)} KB
                              {bulkFilesPreviews.has(f.name) && (
                                <> · {bulkFilesPreviews.get(f.name)!.preview.length} bộ câu hỏi</>
                              )}
                            </span>
                          </div>
                          <button
                            className={`${styles.iconBtn} ${styles.iconBtnDelete}`}
                            onClick={() => removeBulkFile(i)}
                            title="Xóa file này"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Preview loading */}
                  {bulkFilesPreviewing && (
                    <div style={{ textAlign: 'center', padding: '0.75rem', color: '#64748b', fontSize: '0.85rem' }}>
                      <Loader2 size={18} className={styles.spinIcon} /> Đang phân tích file...
                    </div>
                  )}

                  {/* Preview results */}
                  {!bulkFilesPreviewing && totalPreviewedQuestionnaires > 0 && (
                    <div className={styles.importPreviewBox} style={{ marginTop: '0.75rem' }}>
                      <div className={styles.importPreviewHeader}>
                        <span>Tìm thấy: <strong>{totalPreviewedQuestionnaires}</strong> bộ câu hỏi</span>
                        {allPreviewErrors.length > 0 && (
                          <span className={styles.importWarning}>⚠️ {allPreviewErrors.length} cảnh báo</span>
                        )}
                      </div>
                      {allPreviewErrors.length > 0 && (
                        <ul className={styles.importErrorList}>
                          {allPreviewErrors.slice(0, 5).map((e, i) => <li key={i}>{e}</li>)}
                        </ul>
                      )}
                      <div style={{ padding: '0.5rem 0.875rem', maxHeight: '280px', overflowY: 'auto' }}>
                        {Array.from(bulkFilesPreviews.entries()).map(([fname, data]) =>
                          data.preview.map((g, gi) => (
                            <div key={`${fname}-${gi}`} className={styles.fullImportGroupCard}>
                              <div className={styles.fullImportGroupHeader}>
                                <span className={`${styles.badge} ${g.is_active ? styles.badgeActive : styles.badgeDraft}`}>
                                  {g.is_active ? 'Active' : 'Draft'}
                                </span>
                                <strong>{g.title}</strong>
                                <span className={styles.listItemMeta}>{WOUND_TYPE_LABEL[g.wound_type] ?? g.wound_type}</span>
                                <span className={styles.listItemMeta}>• {g.total_questions} câu hỏi</span>
                              </div>
                              {g.description && <div className={styles.fullImportGroupDesc}>{g.description}</div>}
                              <ul className={styles.fullImportQList}>
                                {g.questions_preview.map((q, qi) => (
                                  <li key={qi}>
                                    <span className={styles.questionIndex}>{q.order}</span>
                                    {q.text} <span className={styles.listItemMeta}>({q.answers_count} đáp án)</span>
                                  </li>
                                ))}
                                {g.total_questions > 3 && (
                                  <li style={{ color: '#94a3b8', fontSize: '0.75rem' }}>
                                    ... và {g.total_questions - 3} câu hỏi khác
                                  </li>
                                )}
                              </ul>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}

                  {/* Auto activate */}
                  <label className={styles.checkboxRow} style={{ marginTop: '0.75rem' }}>
                    <input
                      type="checkbox"
                      checked={bulkFilesAutoActivate}
                      onChange={(e) => setBulkFilesAutoActivate(e.target.checked)}
                    />
                    Tự động kích hoạt các bộ vừa import (sẽ deactivate bộ cùng loại đang active)
                  </label>
                </>
              )}

              {/* Results after import */}
              {bulkFilesResult && (
                <div className={styles.importPreviewBox}>
                  <div className={styles.importPreviewHeader} style={{ background: '#f0fdf4' }}>
                    <span>
                      <CheckCircle2 size={14} style={{ color: '#16a34a', marginRight: '0.375rem' }} />
                      Đã import thành công <strong>{bulkFilesResult.imported}</strong> bộ câu hỏi
                    </span>
                  </div>

                  {/* Per-file status */}
                  {bulkFilesResult.file_results.length > 0 && (
                    <div style={{ padding: '0.5rem 0.875rem' }}>
                      {bulkFilesResult.file_results.map((fr, i) => (
                        <div key={i} className={styles.bulkFileResultRow}>
                          <span className={`${styles.badge} ${fr.status === 'ok' ? styles.badgeActive : styles.badgeRed}`}>
                            {fr.status === 'ok' ? '✓' : '✗'}
                          </span>
                          <span className={styles.bulkFileResultName}>{fr.filename}</span>
                          <span className={styles.bulkFileResultMsg}>{fr.message}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Imported questionnaires */}
                  {bulkFilesResult.questionnaires.length > 0 && (
                    <div style={{ padding: '0.5rem 0.875rem', borderTop: '1px solid #e2e8f0' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', marginBottom: '0.375rem', textTransform: 'uppercase' }}>
                        Bộ câu hỏi đã tạo
                      </div>
                      {bulkFilesResult.questionnaires.map((q, i) => (
                        <div key={i} className={styles.bulkFileResultRow}>
                          <span className={`${styles.badge} ${q.is_active ? styles.badgeActive : styles.badgeDraft}`}>
                            {q.is_active ? 'Active' : 'Draft'}
                          </span>
                          <strong style={{ fontSize: '0.8rem' }}>{q.title}</strong>
                          <span className={styles.listItemMeta}>{WOUND_TYPE_LABEL[q.wound_type] ?? q.wound_type}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {bulkFilesResult.errors.length > 0 && (
                    <ul className={styles.importErrorList} style={{ margin: '0.5rem 0.875rem' }}>
                      {bulkFilesResult.errors.slice(0, 8).map((e, i) => <li key={i}>{e}</li>)}
                      {bulkFilesResult.errors.length > 8 && (
                        <li style={{ color: '#94a3b8' }}>... và {bulkFilesResult.errors.length - 8} lỗi khác</li>
                      )}
                    </ul>
                  )}
                </div>
              )}
            </div>

            <div className={styles.modalActions}>
              <button type="button" className={styles.btnSecondary} onClick={closeModal}>
                {bulkFilesResult ? 'Đóng' : 'Hủy'}
              </button>
              {!bulkFilesResult && (
                <button
                  className={styles.btnSubmit}
                  onClick={handleConfirmBulkFiles}
                  disabled={submitting || bulkFiles.length === 0 || bulkFilesPreviewing}
                >
                  {submitting ? <Loader2 size={14} className={styles.spinIcon} /> : <Upload size={14} />}
                  Import {totalPreviewedQuestionnaires > 0 ? `${totalPreviewedQuestionnaires} bộ câu hỏi` : `${bulkFiles.length} file`}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ─── Export Bulk Modal ─── */}
      {modal === 'exportBulk' && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()} style={{ maxWidth: '650px' }}>
            <div className={styles.modalHeader}>
              <h2><Download size={16} /> Export Bộ Câu Hỏi</h2>
              <button className={styles.modalClose} onClick={closeModal}><X size={16} /></button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.fullImportModeInfo}>
                <strong>Xuất bộ câu hỏi ra file</strong> — Chọn một hoặc nhiều bộ câu hỏi để xuất thành file CSV hoặc Excel.
                File xuất ra có thể dùng để re-import.
              </div>

              {/* Format picker */}
              <div className={styles.exportFormatPicker}>
                <span className={styles.exportFormatLabel}>Định dạng:</span>
                <button
                  className={`${styles.exportFormatBtn} ${exportFormat === 'excel' ? styles.exportFormatBtnActive : ''}`}
                  onClick={() => setExportFormat('excel')}
                >
                  <FileSpreadsheet size={14} /> Excel (.xlsx)
                </button>
                <button
                  className={`${styles.exportFormatBtn} ${exportFormat === 'csv' ? styles.exportFormatBtnActive : ''}`}
                  onClick={() => setExportFormat('csv')}
                >
                  <FileSpreadsheet size={14} /> CSV
                </button>
                <button
                  className={`${styles.exportFormatBtn} ${exportFormat === 'docx' ? styles.exportFormatBtnActive : ''}`}
                  onClick={() => setExportFormat('docx')}
                >
                  <Files size={14} /> Word (.docx)
                </button>
                <button
                  className={`${styles.exportFormatBtn} ${exportFormat === 'pdf' ? styles.exportFormatBtnActive : ''}`}
                  onClick={() => setExportFormat('pdf')}
                >
                  <FileQuestion size={14} /> PDF
                </button>
              </div>

              {/* Select all */}
              <div className={styles.exportSelectAll}>
                <label className={styles.checkboxRow}>
                  <input
                    type="checkbox"
                    checked={exportSelectedIds.size === questionnaires.length && questionnaires.length > 0}
                    onChange={toggleAllExport}
                  />
                  Chọn tất cả ({questionnaires.length} bộ)
                </label>
                {exportSelectedIds.size > 0 && (
                  <span className={styles.exportSelectedCount}>
                    Đã chọn: <strong>{exportSelectedIds.size}</strong>
                  </span>
                )}
              </div>

              {/* Questionnaire list */}
              <div className={styles.exportList}>
                {questionnaires.map((q) => (
                  <label key={q.questionnaire_id} className={styles.exportListItem}>
                    <input
                      type="checkbox"
                      checked={exportSelectedIds.has(q.questionnaire_id)}
                      onChange={() => toggleExportId(q.questionnaire_id)}
                    />
                    <span className={`${styles.badge} ${q.is_active ? styles.badgeActive : styles.badgeDraft}`}>
                      {q.is_active ? 'Active' : 'Draft'}
                    </span>
                    <div className={styles.exportListItemInfo}>
                      <strong>{q.title}</strong>
                      <span className={styles.listItemMeta}>
                        {WOUND_TYPE_LABEL[q.wound_type] ?? q.wound_type}
                        {' · '}
                        {(q.questions?.length ?? 0)} câu hỏi
                      </span>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className={styles.modalActions}>
              <button type="button" className={styles.btnSecondary} onClick={closeModal}>Hủy</button>
              <button
                className={styles.btnSubmit}
                onClick={handleBulkExport}
                disabled={exporting || exportSelectedIds.size === 0}
              >
                {exporting ? <Loader2 size={14} className={styles.spinIcon} /> : <Download size={14} />}
                Xuất {exportSelectedIds.size} bộ ({exportFormat.toUpperCase()})
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
