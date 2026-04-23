import React, { useState, useEffect, useRef } from "react";
import * as ExcelJS from "exceljs";
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  BookOpen,
  Activity,
  Layers,
  Loader2,
  RefreshCw,
  Ban,
  Download,
  Upload,
  X,
} from "lucide-react";
import StatCard from "./shared/StatCard";
import { useTranslation } from "react-i18next";
import {
  searchFirstAidGuides,
  getWoundTypes,
  getFirstAidStatistics,
  createFirstAidGuide,
  updateFirstAidGuide,
  deleteFirstAidGuide,
  bulkImportFirstAidGuides,
} from "../../services/firstAidService";
import { useToast } from "../../contexts/ToastContext";
import FirstAidViewModal from "./FirstAidViewModal";
import FirstAidFormModal from "./FirstAidFormModal";
import ConfirmDialog from "../common/ConfirmDialog";
import Pagination from "../common/Pagination";
import styles from "./FirstAidManagement.module.css";

interface Guide {
  firstaidguide_id: string;
  wound_type: string;
  severity: string;
  severity_display?: string;
  sub_type?: string;
  title: string;
  description: string;
  steps: string[];
  supplies_needed: string[];
  dos: string[];
  donts: string[];
  estimated_healing_time?: string;
  source?:
    | {
        name: string;
        url?: string;
      }
    | string; // Support both old string and new object format
  is_active: boolean;
  version: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

interface WoundType {
  wound_type: string;
}

interface Stats {
  total_guides: number;
  wound_types: number;
  active_guides: number;
  wound_type_breakdown?: Record<string, number>;
}

interface FormData {
  wound_type: string;
  severity: string;
  sub_type: string;
  title: string;
  description: string;
  steps: string[];
  dos: string[];
  donts: string[];
  supplies_needed: string[];
  estimated_healing_time: string;
  source: {
    name: string;
    url?: string;
  };
  is_active: boolean;
}

export default function FirstAidManagement() {
  const { t } = useTranslation();
  const { success, error: toastError } = useToast();
  const [guides, setGuides] = useState<Guide[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Loading states for async operations
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeletingGuide, setIsDeletingGuide] = useState<string | null>(null);
  const [isReactivatingGuide, setIsReactivatingGuide] = useState<string | null>(
    null
  );
  const [isDeactivatingGuide, setIsDeactivatingGuide] = useState<string | null>(null);

  // Import/Export States
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Export Modal State
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportGuideList, setExportGuideList] = useState<Guide[]>([]);
  const [exportSelected, setExportSelected] = useState<Set<string>>(new Set());
  const [loadingExportList, setLoadingExportList] = useState(false);

  // Import Preview
  interface ImportPreviewRow {
    rowIndex: number;
    title: string;
    wound_type: string;
    severity: string;
    sub_type: string;
    description: string;
    steps: string[];
    dos: string[];
    donts: string[];
    supplies_needed: string[];
    estimated_healing_time: string;
    sourceName: string;
    sourceUrl: string;
    is_active: boolean;
    selected: boolean;
    error?: string;
  }
  const [showImportPreview, setShowImportPreview] = useState(false);
  const [importPreviewData, setImportPreviewData] = useState<ImportPreviewRow[]>([]);
  // Track filename and total rows for audit log metadata
  const [importFilename, setImportFilename] = useState<string>('');
  const [importTotalRows, setImportTotalRows] = useState<number>(0);
  // false (default) = import as inactive | true = import as active + deactivate existing same-type
  const [importAutoActivate, setImportAutoActivate] = useState<boolean>(false);

  // Pagination state
  const [page, setPage] = useState(1);
  const [limit] = useState(6); // Keep limit at 6 as requested
  const [totalCount, setTotalCount] = useState(0);

  // Confirm dialog state
  const [confirmDialog, setConfirmDialog] = useState({
    isOpen: false,
    title: "",
    message: "",
    variant: "warning" as "danger" | "warning" | "info",
    onConfirm: () => {},
  });

  // Filters
  const [woundTypes, setWoundTypes] = useState<WoundType[]>([]);
  const [selectedWoundType, setSelectedWoundType] = useState("");
  const [selectedSeverity, setSelectedSeverity] = useState("");
  const [selectedActiveStatus, setSelectedActiveStatus] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  // BUG-05 FIX: Separate debounced value — only this triggers the API call
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("");

  // Statistics
  const [stats, setStats] = useState<Stats>({
    total_guides: 0,
    wound_types: 0,
    active_guides: 0,
  });

  // Modal states
  const [showViewModal, setShowViewModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedGuide, setSelectedGuide] = useState<Guide | null>(null);

  // Form data
  const [formData, setFormData] = useState<FormData>({
    wound_type: "abrasion",
    severity: "mild",
    sub_type: "",
    title: "",
    description: "",
    steps: [""],
    dos: [""],
    donts: [""],
    supplies_needed: [""],
    estimated_healing_time: "",
    source: { name: "", url: "" },
    is_active: true,
  });

  // Fetch wound types
  const fetchWoundTypes = async () => {
    try {
      const response = await getWoundTypes();
      if (response.success && response.data) {
        setWoundTypes(response.data);
      }
    } catch (err) {
      console.error("Error fetching wound types:", err);
    }
  };

  // Fetch statistics
  const fetchStatistics = async () => {
    try {
      const response = await getFirstAidStatistics();
      if (response.success && response.data) {
        const statsData = response.data;
        setStats({
          total_guides: statsData.total_guides || 0,
          active_guides: statsData.active_guides || 0,
          wound_types: statsData.wound_type_breakdown
            ? Object.keys(statsData.wound_type_breakdown).length
            : 0,
        });
      }
    } catch (err) {
      console.error("Error fetching statistics:", err);
    }
  };

  // Fetch first aid guides
  const fetchGuides = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        limit,
        offset: (page - 1) * limit,
      };

      // Only add params if they have actual values (not empty strings)
      if (selectedWoundType && selectedWoundType.trim()) {
        params.wound_type = selectedWoundType.trim();
      }
      if (selectedSeverity && selectedSeverity.trim()) {
        params.severity = selectedSeverity.trim();
      }
      if (selectedActiveStatus !== "all") {
        params.is_active = selectedActiveStatus === "true";
      }
      // BUG-05 FIX: Use debouncedSearchTerm (not raw searchTerm) in API call
      if (debouncedSearchTerm && debouncedSearchTerm.trim()) {
        params.search = debouncedSearchTerm.trim();
      }

      const response = await searchFirstAidGuides(params);

      if (response.success && response.data) {
        setGuides(response.data);
        // Total is in extra.total from backend SuccessResponse
        const total = response.extra?.total || response.data.length;
        setTotalCount(total);
      } else if (Array.isArray(response)) {
        setGuides(response);
        setTotalCount(response.length);
      }
    } catch (err: any) {
      console.error("Error fetching guides:", err);
      setError(err.response?.data?.error || "Không thể tải danh sách hướng dẫn sơ cứu");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWoundTypes();
    fetchStatistics();
  }, []);

  // BUG-05 FIX: Debounce effect — wait 400ms after user stops typing
  useEffect(() => {
    if (searchDebounceRef.current) {
      clearTimeout(searchDebounceRef.current);
    }
    searchDebounceRef.current = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 400);
    return () => {
      if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    };
  }, [searchTerm]);

  useEffect(() => {
    setPage(1);
    fetchGuides();
  }, [selectedWoundType, selectedSeverity, selectedActiveStatus, debouncedSearchTerm]);

  useEffect(() => {
    fetchGuides();
  }, [page, limit]);

  // Handle view guide
  const handleViewGuide = (guide: Guide) => {
    setSelectedGuide(guide);
    setShowViewModal(true);
  };

  // Handle open add modal
  const handleOpenAddModal = () => {
    resetForm();
    setShowAddModal(true);
  };

  // Handle open edit modal
  const handleOpenEditModal = (guide: Guide) => {
    setSelectedGuide(guide);
    setFormData({
      wound_type: guide.wound_type,
      severity: guide.severity,
      sub_type: guide.sub_type || "",
      title: guide.title,
      description: guide.description || "",
      steps: guide.steps || [""],
      dos: guide.dos || [""],
      donts: guide.donts || [""],
      supplies_needed: guide.supplies_needed || [""],
      estimated_healing_time: guide.estimated_healing_time || "",
      source:
        typeof guide.source === "string"
          ? { name: guide.source, url: "" }
          : guide.source || { name: "", url: "" },
      is_active: guide.is_active !== undefined ? guide.is_active : true,
    });
    setShowEditModal(true);
  };

  // Reset form
  const resetForm = () => {
    setFormData({
      wound_type: "abrasion",
      severity: "mild",
      sub_type: "",
      title: "",
      description: "",
      steps: [""],
      dos: [""],
      donts: [""],
      supplies_needed: [""],
      estimated_healing_time: "",
      source: { name: "", url: "" },
      is_active: true,
    });
  };

  // Handle array field change
  const handleArrayChange = (
    field: keyof FormData,
    index: number,
    value: string
  ) => {
    setFormData((prev) => {
      const newArray = [...(prev[field] as string[])];
      newArray[index] = value;
      return { ...prev, [field]: newArray };
    });
  };

  // Add array item
  const addArrayItem = (field: keyof FormData) => {
    setFormData((prev) => ({
      ...prev,
      [field]: [...(prev[field] as string[]), ""],
    }));
  };

  // Remove array item
  const removeArrayItem = (field: keyof FormData, index: number) => {
    setFormData((prev) => ({
      ...prev,
      [field]: (prev[field] as string[]).filter((_, i) => i !== index),
    }));
  };

  // Handle add guide
  const handleAddGuide = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    try {
      setIsSubmitting(true);
      const cleanedSteps = formData.steps.filter((s) => s && s.trim());
      const cleanedDos = formData.dos.filter((s) => s && s.trim());
      const cleanedDonts = formData.donts.filter((s) => s && s.trim());
      const cleanedSupplies = formData.supplies_needed.filter(
        (s) => s && s.trim()
      );

      // Client-side validation for required array fields
      if (cleanedSteps.length === 0) {
        toastError("Cần ít nhất một bước sơ cứu");
        return;
      }

      if (cleanedSteps.length < 2) {
        toastError(
          "Vui lòng cung cấp ít nhất 2 bước để có hướng dẫn đầy đủ"
        );
        return;
      }

      if (cleanedDos.length === 0) {
        toastError('Cần ít nhất một khuyến nghị "Nên làm"');
        return;
      }

      if (cleanedDonts.length === 0) {
        toastError('Cần ít nhất một cảnh báo "Không nên làm"');
        return;
      }

      const cleanedData: any = {
        wound_type: formData.wound_type,
        severity: formData.severity,
        title: formData.title.trim(),
        steps: cleanedSteps,
        is_active: formData.is_active,
      };

      if (formData.sub_type) {
        cleanedData.sub_type = formData.sub_type;
      }

      if (formData.description && formData.description.trim()) {
        cleanedData.description = formData.description.trim();
      }

      if (
        formData.estimated_healing_time &&
        formData.estimated_healing_time.trim()
      ) {
        cleanedData.estimated_healing_time =
          formData.estimated_healing_time.trim();
      }

      // Source validation and cleanup
      if (
        formData.source &&
        formData.source.name &&
        formData.source.name.trim()
      ) {
        const sourceObj: any = { name: formData.source.name.trim() };
        if (formData.source.url && formData.source.url.trim()) {
          sourceObj.url = formData.source.url.trim();
        }
        cleanedData.source = sourceObj;
      }

      if (cleanedDos.length > 0) cleanedData.dos = cleanedDos;
      if (cleanedDonts.length > 0) cleanedData.donts = cleanedDonts;
      if (cleanedSupplies.length > 0)
        cleanedData.supplies_needed = cleanedSupplies;

      const response = await createFirstAidGuide(cleanedData);
      if (response.success) {
        setShowAddModal(false);
        resetForm();
        fetchGuides();
        fetchStatistics();
        success("Đã tạo hướng dẫn sơ cứu thành công!");
      } else {
        // Show the actual error message from backend
        toastError(response.message || "Không thể tạo hướng dẫn");
      }
    } catch (err: any) {
      console.error("Error creating guide:", err);
      // Prioritize the message field, then detail, then fallback
      let errorMessage = "Không thể tạo hướng dẫn";
      
      if (err.response?.data?.message) {
        errorMessage = typeof err.response.data.message === 'string' 
          ? err.response.data.message 
          : JSON.stringify(err.response.data.message);
      } else if (err.response?.data?.detail) {
        errorMessage = typeof err.response.data.detail === 'string' 
          ? err.response.data.detail 
          : JSON.stringify(err.response.data.detail);
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      toastError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle edit guide
  const handleEditGuide = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting || !selectedGuide) return;

    try {
      setIsSubmitting(true);
      const cleanedSteps = formData.steps.filter((s) => s.trim());
      const cleanedDos = formData.dos.filter((s) => s.trim());
      const cleanedDonts = formData.donts.filter((s) => s.trim());
      const cleanedSupplies = formData.supplies_needed.filter((s) => s.trim());

      // Client-side validation for required array fields
      if (cleanedSteps.length === 0) {
        toastError("Cần ít nhất một bước sơ cứu");
        return;
      }

      if (cleanedSteps.length < 2) {
        toastError(
          "Vui lòng cung cấp ít nhất 2 bước để có hướng dẫn đầy đủ"
        );
        return;
      }

      if (cleanedDos.length === 0) {
        toastError('Cần ít nhất một khuyến nghị "Nên làm"');
        return;
      }

      if (cleanedDonts.length === 0) {
        toastError('Cần ít nhất một cảnh báo "Không nên làm"');
        return;
      }

      const cleanedData: any = {
        title: formData.title,
        description: formData.description || null,
        steps: cleanedSteps,
        dos: cleanedDos,
        donts: cleanedDonts,
        supplies_needed: cleanedSupplies.length > 0 ? cleanedSupplies : null,
        estimated_healing_time: formData.estimated_healing_time || null,
        source:
          formData.source && formData.source.name
            ? {
                name: formData.source.name.trim(),
                ...(formData.source.url && formData.source.url.trim()
                  ? { url: formData.source.url.trim() }
                  : {}),
              }
            : null,
        is_active: formData.is_active,
        sub_type: formData.sub_type || null,
      };

      const response = await updateFirstAidGuide(
        selectedGuide.firstaidguide_id,
        cleanedData
      );
      if (response.success) {
        setShowEditModal(false);
        resetForm();
        fetchGuides();
        fetchStatistics();
        success("Đã cập nhật hướng dẫn sơ cứu thành công!");
      } else {
        toastError(response.message || "Không thể cập nhật hướng dẫn");
      }
    } catch (err: any) {
      console.error("Error updating guide:", err);
      toastError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "Không thể cập nhật hướng dẫn"
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle delete guide
  const handleDeleteGuide = (guideId: string, guideName: string) => {
    setConfirmDialog({
      isOpen: true,
      title: "Xóa hướng dẫn sơ cứu",
      message: `Bạn có chắc chắn muốn xóa "${guideName}"? Hành động này không thể hoàn tác.`,
      variant: "danger",
      onConfirm: () => handleConfirmDelete(guideId),
    });
  };

  const handleConfirmDelete = async (guideId: string) => {
    setConfirmDialog((prev) => ({ ...prev, isOpen: false }));

    if (isDeletingGuide) return;

    try {
      setIsDeletingGuide(guideId);
      const response = await deleteFirstAidGuide(guideId, false);
      if (response.success) {
        fetchGuides();
        fetchStatistics();
        success("Đã xóa hướng dẫn sơ cứu thành công!");
      } else {
        toastError(response.message || "Không thể xóa hướng dẫn");
      }
    } catch (err: any) {
      console.error("Error deleting guide:", err);
      toastError(err.response?.data?.error || "Không thể xóa hướng dẫn");
    } finally {
      setIsDeletingGuide(null);
    }
  };

  // Handle reactivate guide
  const handleReactivateGuide = async (guide: Guide) => {
    if (isReactivatingGuide) return;

    try {
      setIsReactivatingGuide(guide.firstaidguide_id);

      // Prepare update data - just setting is_active to true
      // The backend will validate if there's a conflict
      const updateData = {
        is_active: true,
      };

      const response = await updateFirstAidGuide(
        guide.firstaidguide_id,
        updateData
      );

      if (response.success) {
        fetchGuides();
        fetchStatistics();
        success("Đã kích hoạt lại hướng dẫn sơ cứu!");
      } else {
        toastError(response.message || "Không thể kích hoạt lại");
      }
    } catch (err: any) {
      toastError(
        err?.response?.data?.detail ?? "Kích hoạt lại hướng dẫn thất bại"
      );
    } finally {
      setIsReactivatingGuide(null);
    }
  };

  // ─── Export & Import Helpers ───────────────────────────────────────────────

  // ─── Open Export Modal: fetch all guides then let user pick ───────────────

  const handleOpenExportModal = async () => {
    try {
      setLoadingExportList(true);
      setShowExportModal(true);
      setExportSelected(new Set());

      let all: Guide[] = [];
      let offset = 0;
      const LIMIT = 100;
      let hasMore = true;

      while (hasMore) {
        const res: any = await searchFirstAidGuides({ limit: LIMIT, offset });
        if (res.data && res.data.length > 0) {
          all = [...all, ...res.data];
          offset += LIMIT;
          if (!res.data || res.data.length < LIMIT) hasMore = false;
          if (res.extra && res.extra.total <= all.length) hasMore = false;
        } else {
          hasMore = false;
        }
      }

      setExportGuideList(all);
      // Default: select all
      setExportSelected(new Set(all.map(g => g.firstaidguide_id)));
    } catch (err) {
      toastError('Không thể tải danh sách hướng dẫn.');
      setShowExportModal(false);
    } finally {
      setLoadingExportList(false);
    }
  };

  // ─── Confirm Export: generate Excel from selected guides ──────────────────
  const handleConfirmExport = async () => {
    const guidesToExport = exportGuideList.filter(g => exportSelected.has(g.firstaidguide_id));
    if (guidesToExport.length === 0) {
      toastError('Chưa chọn hướng dẫn nào để xuất.');
      return;
    }

    try {
      setExporting(true);

      // Mapping enum → Vietnamese (khớp format import)
      const woundTypeViMap: Record<string, string> = {
        abrasion: 'Trầy xước', bruise: 'Bầm tím', burn: 'Bỏng',
        cut: 'Vết cắt', acne: 'Mụn trứng cá', fungal: 'Nấm da', psoriasis: 'Vảy nến',
      };
      const severityViMap: Record<string, string> = {
        mild: 'Nhẹ', moderate: 'Trung bình', severe: 'Nặng', general: '',
      };

      const workbook = new ExcelJS.Workbook();
      // Sheet name khớp file mẫu
      const worksheet = workbook.addWorksheet('Hướng dẫn sơ cứu');

      // Headers — khớp chính xác với huong_dan_so_cuu_skinaid_v2.xlsx
      const headers = [
        'Tiêu đề', 'Loại vết thương', 'Mức độ', 'Phân loại phụ',
        'Mô tả', 'Các bước thực hiện', 'Nên làm', 'Không nên làm',
        'Vật tư y tế', 'Thời gian phục hồi', 'Nguồn tham khảo', 'URL nguồn', 'Trạng thái',
      ];
      const headerRow = worksheet.addRow(headers);
      headerRow.eachCell((cell) => {
        cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF17805F' } };
        cell.font = { color: { argb: 'FFFFFFFF' }, bold: true };
        cell.alignment = { vertical: 'middle', horizontal: 'center' };
        cell.border = {
          top: { style: 'thin', color: { argb: 'FFD1D5DB' } },
          left: { style: 'thin', color: { argb: 'FFD1D5DB' } },
          bottom: { style: 'thin', color: { argb: 'FFD1D5DB' } },
          right: { style: 'thin', color: { argb: 'FFD1D5DB' } },
        };
      });

      guidesToExport.forEach(guide => {
        const getSourceName = (s: any) => (!s ? '' : typeof s === 'string' ? s : s.name || '');
        const getSourceUrl  = (s: any) => (!s || typeof s === 'string' ? '' : s.url || '');

        const woundTypeVi = woundTypeViMap[guide.wound_type?.toLowerCase()] || guide.wound_type || '';
        const severityVi  = severityViMap[guide.severity?.toLowerCase()] ?? guide.severity ?? '';

        const row = worksheet.addRow([
          guide.title                      || '',
          woundTypeVi,
          severityVi,
          guide.sub_type                   || '',
          guide.description                || '',
          (guide.steps           || []).join('\n'),
          (guide.dos             || []).join('\n'),
          (guide.donts           || []).join('\n'),
          (guide.supplies_needed || []).join('\n'),
          guide.estimated_healing_time     || '',
          getSourceName(guide.source),
          getSourceUrl(guide.source),
          guide.is_active ? 'Hoạt động' : 'Không hoạt động',
        ]);

        row.eachCell({ includeEmpty: true }, (cell) => {
          cell.alignment = { vertical: 'top', horizontal: 'left', wrapText: true };
          cell.border = {
            top:    { style: 'thin', color: { argb: 'FFD1D5DB' } },
            left:   { style: 'thin', color: { argb: 'FFD1D5DB' } },
            bottom: { style: 'thin', color: { argb: 'FFD1D5DB' } },
            right:  { style: 'thin', color: { argb: 'FFD1D5DB' } },
          };
        });
      });

      worksheet.columns = [
        { width: 30 }, { width: 16 }, { width: 14 }, { width: 16 },
        { width: 35 }, { width: 50 }, { width: 40 }, { width: 40 },
        { width: 28 }, { width: 20 }, { width: 22 }, { width: 32 }, { width: 16 },
      ];

      const buffer = await workbook.xlsx.writeBuffer();
      const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const today = new Date().toISOString().split('T')[0];
      link.setAttribute('download', `huong_dan_so_cuu_${today}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      success(`Đã xuất ${guidesToExport.length} hướng dẫn thành công!`);
      setShowExportModal(false);
      setExportGuideList([]);
      setExportSelected(new Set());
    } catch (err) {
      console.error('Export error', err);
      toastError('Có lỗi xảy ra khi xuất file.');
    } finally {
      setExporting(false);
    }
  };

  const handleImportExcel = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const arrayBuffer = await file.arrayBuffer();
      const workbook = new ExcelJS.Workbook();
      await workbook.xlsx.load(arrayBuffer);

      const worksheet = workbook.worksheets[0];
      if (!worksheet) {
        toastError("File Excel không hợp lệ hoặc trống.");
        return;
      }

      const rows: any[] = [];
      worksheet.eachRow((row, rowNumber) => {
        if (rowNumber > 1) rows.push({ values: row.values, rowNumber });
      });

      if (rows.length === 0) {
        toastError("Không tìm thấy dữ liệu trong file.");
        return;
      }

      const wMap: Record<string, string> = {
        'bỏng': 'burn', 'trầy xước': 'abrasion', 'vết cắt': 'cut', 'cắt': 'cut',
        'bầm tím': 'bruise', 'mụn': 'acne', 'mụn trứng cá': 'acne', 'nấm': 'fungal', 'nấm da': 'fungal', 'vảy nến': 'psoriasis',
      };

      const parsed: ImportPreviewRow[] = rows.map(({ values: row, rowNumber }) => {
        const title = String(row[1] || '').trim();
        let wound_type = String(row[2] || '').trim();
        let severity = String(row[3] || '').trim();

        // Normalize wound type first (needed for severity check)
        wound_type = wMap[wound_type.toLowerCase()] || wound_type;

        // Wound types that don't require severity
        const noSeverityTypes = ['psoriasis', 'fungal'];

        // Normalize severity
        if (severity) {
          const s = severity.toLowerCase();
          if (s === 'nhẹ') severity = 'mild';
          else if (s === 'vừa' || s === 'trung bình') severity = 'moderate';
          else if (s === 'nặng' || s === 'rất nặng') severity = 'severe';
        } else if (noSeverityTypes.includes(wound_type.toLowerCase())) {
          severity = 'general'; // Auto-set for psoriasis/fungal
        }

        const parseArray = (str: string) => str.split('\n').map(s => s.trim()).filter(s => s);

        let error: string | undefined;
        if (!wound_type) error = 'Thiếu loại vết thương';
        else if (!severity && !noSeverityTypes.includes(wound_type.toLowerCase())) error = 'Thiếu mức độ nghiêm trọng';
        if (!title) error = 'Thiếu tiêu đề';

        return {
          rowIndex: rowNumber,
          title,
          wound_type,
          severity,
          sub_type: String(row[4] || '').trim(),
          description: String(row[5] || '').trim(),
          steps: parseArray(String(row[6] || '')),
          dos: parseArray(String(row[7] || '')),
          donts: parseArray(String(row[8] || '')),
          supplies_needed: parseArray(String(row[9] || '')),
          estimated_healing_time: String(row[10] || '').trim(),
          sourceName: String(row[11] || '').trim(),
          sourceUrl: String(row[12] || '').trim(),
          is_active: String(row[13] || '').trim().toLowerCase() === 'hoạt động',
          selected: !error,
          error,
        };
      });

      setImportPreviewData(parsed);
      setImportFilename(file.name);         // save for audit log
      setImportTotalRows(parsed.length);    // save total rows parsed
      setShowImportPreview(true);
    } catch (err) {
      console.error("Parse file error:", err);
      toastError("Lỗi đọc file Excel. Vui lòng thử lại bằng file mẫu.");
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleConfirmImport = async () => {
    const selectedRows = importPreviewData.filter(r => r.selected && !r.error);
    if (selectedRows.length === 0) {
      toastError('Không có dòng nào được chọn để import.');
      return;
    }

    try {
      setImporting(true);

      // Build bulk payload — includes metadata for audit log
      const skippedRows = importPreviewData.filter(r => r.error).length;

      // Resolve is_active: unchecked = always inactive, checked = always active
      const resolveActive = (): boolean => importAutoActivate;

      const payload = {
        guides: selectedRows.map(row => ({
          title: row.title,
          wound_type: row.wound_type,
          severity: row.severity,
          sub_type: row.sub_type || undefined,
          description: row.description || undefined,
          steps: row.steps.length > 0 ? row.steps : ['Liên hệ cứu thương'],
          dos: row.dos,
          donts: row.donts,
          supplies_needed: row.supplies_needed,
          estimated_healing_time: row.estimated_healing_time || undefined,
          source: { name: row.sourceName || 'Hệ thống', url: row.sourceUrl || undefined },
          is_active: resolveActive(),
        })),
        filename: importFilename,
        total_rows_in_file: importTotalRows,
        skipped_rows: skippedRows,
        auto_deactivate_conflicts: importAutoActivate,
      };

      const response = await bulkImportFirstAidGuides(payload);
      const result = response.data;

      // Update preview rows that failed
      if (result.failed_count > 0) {
        setImportPreviewData(prev => prev.map(r => {
          const failedItem = result.failed_items.find(
            fi => selectedRows[fi.index]?.rowIndex === r.rowIndex
          );
          if (failedItem) return { ...r, error: failedItem.reason, selected: false };
          return r;
        }));
        toastError(
          `${result.failed_count} dòng bị lỗi:\n` +
          result.failed_items
            .map(f => `• ${f.title || `Dòng ${f.index + 1}`}: ${f.reason}`)
            .join('\n')
        );
      }

      if (result.success_count > 0) {
        success(`Đã import thành công ${result.success_count}/${selectedRows.length} hướng dẫn!`);
        fetchGuides();
        fetchStatistics();
      }

      // Close modal only if all rows succeeded
      if (result.failed_count === 0) {
        setShowImportPreview(false);
        setImportPreviewData([]);
        setImportFilename('');
        setImportTotalRows(0);
        setImportAutoActivate(false);
      }
    } catch (err) {
      console.error('Import error:', err);
      toastError('Có lỗi xảy ra khi import.');
    } finally {
      setImporting(false);
    }
  };

  const togglePreviewRow = (rowIndex: number) => {
    setImportPreviewData(prev => prev.map(r =>
      r.rowIndex === rowIndex ? { ...r, selected: !r.selected } : r
    ));
  };

  const toggleAllPreviewRows = (checked: boolean) => {
    setImportPreviewData(prev => prev.map(r =>
      r.error ? r : { ...r, selected: checked }
    ));
  };

  // Handle deactivate guide
  const handleDeactivateGuide = async (guide: Guide) => {
    if (isDeactivatingGuide) return;

    try {
      setIsDeactivatingGuide(guide.firstaidguide_id);

      const updateData = {
        is_active: false,
      };

      const response = await updateFirstAidGuide(
        guide.firstaidguide_id,
        updateData
      );

      if (response.success) {
        fetchGuides();
        fetchStatistics();
        success("Đã vô hiệu hóa hướng dẫn sơ cứu!");
      } else {
        toastError(response.message || "Không thể vô hiệu hóa");
      }
    } catch (err: any) {
      console.error("Error deactivating guide:", err);
      toastError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "Không thể vô hiệu hóa"
      );
    } finally {
      setIsDeactivatingGuide(null);
    }
  };

  const getSeverityBadgeClass = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "mild":
        return styles.badgeSuccess;
      case "moderate":
        return styles.badgeWarning;
      case "severe":
        return styles.badgeDanger;
      default:
        return styles.badgeDefault;
    }
  };

  const formatWoundType = (woundType: string) => {
    const typeMap: Record<string, string> = {
      abrasion: "Trầy xước",
      bruise: "Bầm tím",
      burn: "Bỏng",
      cut: "Vết cắt",
      acne: "Mụn",
      fungal: "Nấm da",
      psoriasis: "Vảy nến",
    };
    return typeMap[woundType.toLowerCase()] || woundType;
  };

  const formatSeverity = (severity: string) => {
    const sevMap: Record<string, string> = {
      mild: "Nhẹ",
      moderate: "Vừa",
      severe: "Nặng",
      general: "Chung",
    };
    return sevMap[severity.toLowerCase()] || severity;
  };

  return (
    <div className={styles.firstaidManagementPage}>
      <title>{t("title.admin_first_aid")}</title>
      <div className={styles.pageHeader}>
        <div className={styles.pageTitle}>
          <h1>{t("admin.first_aid.title")}</h1>
          <p>{t("admin.first_aid.subtitle")}</p>
        </div>
        <div className={styles.headerActions}>
          <input 
            type="file" 
            accept=".xlsx,.csv" 
            style={{ display: 'none' }} 
            ref={fileInputRef} 
            onChange={handleImportExcel} 
          />
          <button 
            className={styles.btnOutline} 
            onClick={() => fileInputRef.current?.click()} 
            disabled={importing || exporting}
            title="Import dữ liệu sơ cứu từ file Excel"
          >
            {importing ? <Loader2 size={16} className={styles.spin} /> : <Upload size={16} />} 
            Import
          </button>
          

          {/* 1 nút Export duy nhất → mở modal chọn */}
          <button
            className={styles.btnOutline}
            onClick={handleOpenExportModal}
            disabled={importing || exporting}
            title="Chọn hướng dẫn và xuất file Excel"
          >
            {exporting ? <Loader2 size={16} className={styles.spin} /> : <Download size={16} />}
            Export
          </button>

          <button 
            className={styles.btnPrimary} 
            onClick={handleOpenAddModal} 
            disabled={importing || exporting}
          >
            <Plus size={18} />
            {t("admin.first_aid.add_guidance")}
          </button>
        </div>
      </div>

      <div className={styles.statsGrid}>
        <StatCard
          icon={BookOpen}
          value={stats.total_guides}
          label={t("admin.first_aid.total_guides")}
          color="primary"
        />
        <StatCard
          icon={Activity}
          value={stats.active_guides}
          label={t("admin.first_aid.active_guides")}
          color="green"
        />
        <StatCard
          icon={Layers}
          value={stats.wound_types}
          label={t("admin.first_aid.wound_types")}
          color="purple"
        />
      </div>

      <div className={styles.filtersSection}>
        <div className={styles.filterGroup}>
          <label>{t("admin.first_aid.search_placeholder")}</label>
          <div style={{ position: "relative" }}>
            <input
              type="text"
              placeholder={t("admin.first_aid.search_placeholder")}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: "100%",
                padding: "0.625rem 0.75rem",
                paddingRight: "2.5rem",
                border: "1px solid #e2e8f0",
                borderRadius: "0.5rem",
                fontSize: "0.875rem",
              }}
            />
            <Search
              size={18}
              style={{
                position: "absolute",
                right: "0.75rem",
                top: "50%",
                transform: "translateY(-50%)",
                color: "#64748b",
              }}
            />
          </div>
        </div>
        <div className={styles.filterGroup}>
          <label>{t("admin.first_aid.filter_wound_type")}</label>
          <select
            value={selectedWoundType}
            onChange={(e) => setSelectedWoundType(e.target.value)}
          >
            <option value="">
              {t("admin.first_aid.filter_wound_type_all")}
            </option>
            {woundTypes.map((type) => (
              <option key={type.wound_type} value={type.wound_type}>
                {t(`admin.first_aid_form.options.${type.wound_type}`) ||
                  formatWoundType(type.wound_type)}
              </option>
            ))}
          </select>
        </div>
        <div className={styles.filterGroup}>
          <label>{t("admin.first_aid.filter_severity")}</label>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
          >
            <option value="">{t("admin.first_aid.filter_severity_all")}</option>
            <option value="mild">
              {t("admin.first_aid_form.options.mild")}
            </option>
            <option value="moderate">
              {t("admin.first_aid_form.options.moderate")}
            </option>
            <option value="severe">
              {t("admin.first_aid_form.options.severe")}
            </option>
          </select>
        </div>
        <div className={styles.filterGroup}>
          <label>{t("admin.first_aid.filter_status")}</label>
          <select
            value={selectedActiveStatus}
            onChange={(e) => setSelectedActiveStatus(e.target.value)}
          >
            <option value="all">
              {t("admin.first_aid.filter_status_all")}
            </option>
            <option value="true">
              {t("admin.first_aid.filter_status_active")}
            </option>
            <option value="false">
              {t("admin.first_aid.filter_status_inactive")}
            </option>
          </select>
        </div>
      </div>

      {/* Guides count */}
      <div
        className={styles.usersCount}
        style={{ marginBottom: "1rem", fontSize: "0.9rem", color: "#64748b" }}
      >
        Tổng hướng dẫn ({totalCount})
        {totalCount > 0 && (
          <span
            style={{ marginLeft: "1rem", color: "#666", fontSize: "0.9rem" }}
          >
            {t("admin.user_management.showing", {
              start: (page - 1) * limit + 1,
              end: Math.min(page * limit, totalCount),
              total: totalCount,
            })}
          </span>
        )}
      </div>

      {loading && (
        <div className={styles.loadingState}>
          <div className={styles.loadingSpinner}></div>
          <p>{t("admin.first_aid.loading")}</p>
        </div>
      )}

      {error && (
        <div className={styles.errorState}>
          <div className={styles.errorIcon}>⚠️</div>
          <p>{error}</p>
          <button onClick={fetchGuides} className={styles.btnRetry}>
            {t("admin.dashboard.retry")}
          </button>
        </div>
      )}

      {!loading && !error && (
        <div className={styles.guidesGrid}>
          {guides.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>📋</div>
              <p>{t("admin.first_aid.no_guides")}</p>
              <p className={styles.emptySubtitle}>
                {t("admin.first_aid.try_adjusting")}
              </p>
            </div>
          ) : (
            guides.map((guide) => (
              <div
                key={guide.firstaidguide_id}
                className={`${styles.guideCard} ${
                  !guide.is_active ? styles.guideCardInactive : ""
                }`}
              >
                <div className={styles.guideCardHeader}>
                  <div className={styles.guideInfo}>
                    <h3
                      style={{
                        textDecoration: !guide.is_active
                          ? "line-through"
                          : "none",
                      }}
                    >
                      {guide.title}
                    </h3>
                    <div className={styles.guideMeta}>
                      <span
                        className={`${styles.badge} ${styles.badgeWoundType}`}
                      >
                        {/* BUG-02 FIX: Use formatWoundType() for Vietnamese display */}
                        {formatWoundType(guide.wound_type)}
                      </span>
                      {guide.sub_type && (
                        <span
                          className={`${styles.badge} ${styles.badgeDefault}`}
                        >
                          {guide.sub_type}
                        </span>
                      )}
                      <span
                        className={`${styles.badge} ${getSeverityBadgeClass(
                          guide.severity
                        )}`}
                      >
                        {t(`admin.first_aid_form.options.${guide.severity}`) ||
                          guide.severity_display ||
                          guide.severity}
                      </span>
                      <span className={styles.guideDate}>
                        {t("admin.first_aid_view.labels.last_updated")}:{" "}
                        {new Date(guide.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>

                <div className={styles.guideCardBody}>
                  {guide.description && (
                    <p className={styles.guideDescription}>
                      {guide.description}
                    </p>
                  )}

                  <div className={styles.guideStepsPreview}>
                    <p className={styles.stepsTitle}>
                      {t("admin.first_aid_view.labels.steps")}:
                    </p>
                    <ul className={styles.stepsList}>
                      {guide.steps &&
                        guide.steps.slice(0, 3).map((step, index) => (
                          <li key={index}>
                            <span className={styles.stepNumber}>
                              {index + 1}.{" "}
                            </span>
                            <span className={styles.stepText}>{step}</span>
                          </li>
                        ))}
                    </ul>
                    {guide.steps && guide.steps.length > 3 && (
                      <p className={styles.stepsMore}>
                        +{guide.steps.length - 3}{" "}
                        {t("admin.first_aid.more_steps")}
                      </p>
                    )}
                  </div>

                  <div className={styles.guideCardActions}>
                    <button
                      className={styles.btnViewFull}
                      onClick={() => handleViewGuide(guide)}
                    >
                      {t("admin.first_aid.view_details")}
                    </button>
                    <button
                      className={styles.btnEdit}
                      onClick={() => handleOpenEditModal(guide)}
                      title="Edit"
                    >
                      <Edit2 size={16} />
                    </button>
                    {guide.is_active ? (
                      <>
                        <button
                          className={`${styles.btnEdit} ${styles.btnDeactivate}`}
                          onClick={() => handleDeactivateGuide(guide)}
                          title="Deactivate"
                          disabled={
                            isDeactivatingGuide === guide.firstaidguide_id
                          }
                          style={{ color: "#f59e0b", borderColor: "#f59e0b" }}
                        >
                          {isDeactivatingGuide === guide.firstaidguide_id ? (
                            <Loader2 size={16} className={styles.spinning} />
                          ) : (
                            <Ban size={16} />
                          )}
                        </button>
                        <button
                          className={styles.btnDelete}
                          onClick={() =>
                            handleDeleteGuide(
                              guide.firstaidguide_id,
                              guide.title
                            )
                          }
                          title="Delete"
                          disabled={isDeletingGuide === guide.firstaidguide_id}
                        >
                          {isDeletingGuide === guide.firstaidguide_id ? (
                            <Loader2 size={16} className={styles.spinning} />
                          ) : (
                            <Trash2 size={16} />
                          )}
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          className={`${styles.btnEdit} ${styles.btnReactivate}`}
                          onClick={() => handleReactivateGuide(guide)}
                          title="Reactivate"
                          disabled={
                            isReactivatingGuide === guide.firstaidguide_id
                          }
                          style={{ color: "#1E9378", borderColor: "#1E9378" }}
                        >
                          {isReactivatingGuide === guide.firstaidguide_id ? (
                            <Loader2 size={16} className={styles.spinning} />
                          ) : (
                            <RefreshCw size={16} />
                          )}
                        </button>
                        <button
                          className={styles.btnDelete}
                          onClick={() =>
                            handleDeleteGuide(
                              guide.firstaidguide_id,
                              guide.title
                            )
                          }
                          title="Delete"
                          disabled={isDeletingGuide === guide.firstaidguide_id}
                        >
                          {isDeletingGuide === guide.firstaidguide_id ? (
                            <Loader2 size={16} className={styles.spinning} />
                          ) : (
                            <Trash2 size={16} />
                          )}
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {!loading && !error && totalCount > 0 && (
        <Pagination
          currentPage={page}
          totalPages={Math.ceil(totalCount / limit)}
          totalItems={totalCount}
          itemsPerPage={limit}
          onPageChange={setPage}
          showInfo={true}
          className={styles.centeredPagination}
        />
      )}

      <FirstAidViewModal
        isOpen={showViewModal}
        guide={selectedGuide}
        onClose={() => setShowViewModal(false)}
        formatWoundType={formatWoundType}
        getSeverityBadgeClass={getSeverityBadgeClass}
      />

      <FirstAidFormModal
        isOpen={showAddModal || showEditModal}
        mode={showEditModal ? "edit" : "add"}
        formData={formData}
        onClose={() => {
          setShowAddModal(false);
          setShowEditModal(false);
        }}
        onSubmit={showEditModal ? handleEditGuide : handleAddGuide}
        onFormChange={setFormData}
        onArrayChange={handleArrayChange}
        onAddArrayItem={addArrayItem}
        onRemoveArrayItem={removeArrayItem}
        isSubmitting={isSubmitting}
      />

      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        variant={confirmDialog.variant}
        confirmText="Delete"
        cancelText="Cancel"
        onConfirm={confirmDialog.onConfirm}
        onCancel={() =>
          setConfirmDialog((prev) => ({ ...prev, isOpen: false }))
        }
        isLoading={isDeletingGuide !== null}
      />

      {/* Import Preview Modal */}
      {showImportPreview && (
        <div className={styles.modalOverlay} onClick={() => !importing && setShowImportPreview(false)}>
          <div className={styles.importPreviewModal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div>
                <h2>Xem trước dữ liệu Import</h2>
                <p className={styles.modalSubtitle}>
                  {importPreviewData.filter(r => r.selected && !r.error).length} / {importPreviewData.length} dòng được chọn
                  {importPreviewData.some(r => r.error) && (
                    <span style={{ color: '#ef4444', marginLeft: '0.5rem' }}>
                      • {importPreviewData.filter(r => r.error).length} dòng lỗi
                    </span>
                  )}
                </p>
              </div>

              {/* Checkbox tự động kích hoạt */}
              <label style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                fontSize: '13px', cursor: 'pointer', userSelect: 'none',
                padding: '6px 10px', borderRadius: '8px',
                background: importAutoActivate ? '#f0fdf4' : '#f9fafb',
                border: `1px solid ${importAutoActivate ? '#86efac' : '#e5e7eb'}`,
                transition: 'all 0.2s',
              }}>
                <input
                  type="checkbox"
                  checked={importAutoActivate}
                  onChange={e => setImportAutoActivate(e.target.checked)}
                  disabled={importing}
                  style={{ width: '15px', height: '15px', accentColor: '#17805f', cursor: 'pointer' }}
                />
                <span>
                  Tự động <strong>kích hoạt</strong> và vô hiệu hóa các bộ cùng loại
                </span>
              </label>

              <button className={styles.modalClose} onClick={() => !importing && setShowImportPreview(false)}>
                <X size={20} />
              </button>
            </div>
            <div className={styles.importPreviewBody}>
              <table className={styles.previewTable}>
                <thead>
                  <tr>
                    <th style={{ width: '40px' }}>
                      <input
                        type="checkbox"
                        checked={importPreviewData.filter(r => !r.error).every(r => r.selected)}
                        onChange={e => toggleAllPreviewRows(e.target.checked)}
                      />
                    </th>
                    <th>#</th>
                    <th>Tiêu đề</th>
                    <th>Loại</th>
                    <th>Mức độ</th>
                    <th>Số bước</th>
                    <th>Nguồn</th>
                    <th>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {importPreviewData.map(row => (
                    <tr key={row.rowIndex} className={row.error ? styles.previewRowError : row.selected ? styles.previewRowSelected : ''}>
                      <td>
                        <input
                          type="checkbox"
                          checked={row.selected}
                          disabled={!!row.error}
                          onChange={() => togglePreviewRow(row.rowIndex)}
                        />
                      </td>
                      <td>{row.rowIndex}</td>
                      <td>
                        <div className={styles.previewTitle}>{row.title || '—'}</div>
                        {row.description && <div className={styles.previewDesc}>{row.description.substring(0, 60)}...</div>}
                        {row.error && <div className={styles.previewError}>{row.error}</div>}
                      </td>
                      <td>{formatWoundType(row.wound_type) || '—'}</td>
                      <td>
                        <span className={`${styles.badge} ${getSeverityBadgeClass(row.severity)}`}>
                          {formatSeverity(row.severity)}
                        </span>
                      </td>
                      <td>{row.steps.length}</td>
                      <td>
                        <div>{row.sourceName || '—'}</div>
                        {row.sourceUrl && <div className={styles.previewUrl}>{row.sourceUrl.substring(0, 30)}...</div>}
                      </td>
                      <td>
                        <span className={`${styles.badge} ${importAutoActivate ? styles.badgeSuccess : styles.badgeDefault}`}>
                          {importAutoActivate ? 'Hoạt động' : 'Không hoạt động'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className={styles.importPreviewFooter}>
              <button
                className={styles.btnOutline}
                onClick={() => { setShowImportPreview(false); setImportPreviewData([]); }}
                disabled={importing}
              >
                Hủy
              </button>
              <button
                className={styles.btnPrimary}
                onClick={handleConfirmImport}
                disabled={importing || importPreviewData.filter(r => r.selected && !r.error).length === 0}
              >
                {importing ? <><Loader2 size={16} className={styles.spin} /> Đang import...</> : <>
                  <Upload size={16} /> Import {importPreviewData.filter(r => r.selected && !r.error).length} dòng
                </>}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* ─── Export Modal ─────────────────────────────────────────────── */}
      {showExportModal && (
        <div className={styles.modalOverlay} onClick={() => !exporting && setShowExportModal(false)}>
          <div className={styles.importPreviewModal} onClick={e => e.stopPropagation()} style={{ maxWidth: '760px' }}>
            <div className={styles.modalHeader}>
              <div>
                <h2>Chọn hướng dẫn để xuất Excel</h2>
                <p className={styles.modalSubtitle}>
                  {exportSelected.size} / {exportGuideList.length} hướng dẫn được chọn
                </p>
              </div>
              <button className={styles.modalClose} onClick={() => !exporting && setShowExportModal(false)}>
                <X size={20} />
              </button>
            </div>

            <div className={styles.importPreviewBody}>
              {loadingExportList ? (
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                  <Loader2 size={28} className={styles.spin} style={{ color: '#17805f' }} />
                  <p style={{ marginTop: '0.5rem', color: '#6b7280' }}>Đang tải danh sách...</p>
                </div>
              ) : exportGuideList.length === 0 ? (
                <p style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>Không có hướng dẫn nào.</p>
              ) : (
                <table className={styles.previewTable}>
                  <thead>
                    <tr>
                      <th style={{ width: '40px' }}>
                        <input
                          type="checkbox"
                          checked={exportSelected.size === exportGuideList.length && exportGuideList.length > 0}
                          onChange={e => {
                            if (e.target.checked) {
                              setExportSelected(new Set(exportGuideList.map(g => g.firstaidguide_id)));
                            } else {
                              setExportSelected(new Set());
                            }
                          }}
                        />
                      </th>
                      <th>Tiêu đề</th>
                      <th>Loại vết thương</th>
                      <th>Mức độ</th>
                      <th>Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody>
                    {exportGuideList.map(guide => (
                      <tr
                        key={guide.firstaidguide_id}
                        className={exportSelected.has(guide.firstaidguide_id) ? styles.previewRowSelected : ''}
                        style={{ cursor: 'pointer' }}
                        onClick={() => {
                          setExportSelected(prev => {
                            const next = new Set(prev);
                            if (next.has(guide.firstaidguide_id)) next.delete(guide.firstaidguide_id);
                            else next.add(guide.firstaidguide_id);
                            return next;
                          });
                        }}
                      >
                        <td onClick={e => e.stopPropagation()}>
                          <input
                            type="checkbox"
                            checked={exportSelected.has(guide.firstaidguide_id)}
                            onChange={() => {
                              setExportSelected(prev => {
                                const next = new Set(prev);
                                if (next.has(guide.firstaidguide_id)) next.delete(guide.firstaidguide_id);
                                else next.add(guide.firstaidguide_id);
                                return next;
                              });
                            }}
                          />
                        </td>
                        <td>
                          <div className={styles.previewTitle}>{guide.title}</div>
                          {guide.sub_type && <div className={styles.previewDesc}>{guide.sub_type}</div>}
                        </td>
                        <td>{formatWoundType(guide.wound_type)}</td>
                        <td>
                          <span className={`${styles.badge} ${getSeverityBadgeClass(guide.severity)}`}>
                            {formatSeverity(guide.severity)}
                          </span>
                        </td>
                        <td>
                          <span className={`${styles.badge} ${guide.is_active ? styles.badgeSuccess : styles.badgeDefault}`}>
                            {guide.is_active ? 'Hoạt động' : 'Tắt'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className={styles.importPreviewFooter}>
              <button
                className={styles.btnOutline}
                onClick={() => { setShowExportModal(false); setExportGuideList([]); setExportSelected(new Set()); }}
                disabled={exporting}
              >
                Hủy
              </button>
              <button
                className={styles.btnPrimary}
                onClick={handleConfirmExport}
                disabled={exporting || exportSelected.size === 0 || loadingExportList}
              >
                {exporting
                  ? <><Loader2 size={16} className={styles.spin} /> Đang xuất...</>
                  : <><Download size={16} /> Xuất {exportSelected.size} hướng dẫn</>
                }
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
