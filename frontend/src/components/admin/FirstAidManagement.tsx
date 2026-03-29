import React, { useState, useEffect } from "react";
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  BookOpen,
  Activity,
  AlertCircle,
  Loader2,
  RefreshCw,
  Ban,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import {
  searchFirstAidGuides,
  getWoundTypes,
  getFirstAidStatistics,
  createFirstAidGuide,
  updateFirstAidGuide,
  deleteFirstAidGuide,
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
  const [isDeactivatingGuide, setIsDeactivatingGuide] = useState<string | null>(
    null
  );

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
      if (searchTerm && searchTerm.trim()) {
        params.search = searchTerm.trim();
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
      setError(err.response?.data?.error || "Failed to fetch first aid guides");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWoundTypes();
    fetchStatistics();
  }, []);

  useEffect(() => {
    setPage(1);
    fetchGuides();
  }, [selectedWoundType, selectedSeverity, selectedActiveStatus, searchTerm]);

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
        toastError("At least one step is required");
        return;
      }

      if (cleanedSteps.length < 2) {
        toastError(
          "Please provide at least 2 steps for comprehensive guidance"
        );
        return;
      }

      if (cleanedDos.length === 0) {
        toastError('At least one "Do" recommendation is required');
        return;
      }

      if (cleanedDonts.length === 0) {
        toastError('At least one "Don\'t" warning is required');
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
        success("First aid guide created successfully!");
      } else {
        // Show the actual error message from backend
        toastError(response.message || "Failed to create guide");
      }
    } catch (err: any) {
      console.error("Error creating guide:", err);
      // Prioritize the message field, then detail, then fallback
      let errorMessage = "Failed to create guide";
      
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
        toastError("At least one step is required");
        return;
      }

      if (cleanedSteps.length < 2) {
        toastError(
          "Please provide at least 2 steps for comprehensive guidance"
        );
        return;
      }

      if (cleanedDos.length === 0) {
        toastError('At least one "Do" recommendation is required');
        return;
      }

      if (cleanedDonts.length === 0) {
        toastError('At least one "Don\'t" warning is required');
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
        success("First aid guide updated successfully!");
      } else {
        toastError(response.message || "Failed to update guide");
      }
    } catch (err: any) {
      console.error("Error updating guide:", err);
      toastError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "Failed to update guide"
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle delete guide
  const handleDeleteGuide = (guideId: string, guideName: string) => {
    setConfirmDialog({
      isOpen: true,
      title: "Delete First Aid Guide",
      message: `Are you sure you want to delete "${guideName}"? This action cannot be undone.`,
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
        success("First aid guide deleted successfully!");
      } else {
        toastError(response.message || "Failed to delete guide");
      }
    } catch (err: any) {
      console.error("Error deleting guide:", err);
      toastError(err.response?.data?.error || "Failed to delete guide");
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
        success("First aid guide reactivated successfully!");
      } else {
        toastError(response.message || "Failed to reactivate guide");
      }
    } catch (err: any) {
      console.error("Error reactivating guide:", err);
      toastError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "Failed to reactivate guide"
      );
    } finally {
      setIsReactivatingGuide(null);
    }
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
        success("First aid guide deactivated successfully!");
      } else {
        toastError(response.message || "Failed to deactivate guide");
      }
    } catch (err: any) {
      console.error("Error deactivating guide:", err);
      toastError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "Failed to deactivate guide"
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
      abrasion: "Scratch / Abrasion",
      bruise: "Bruise / Contusion",
      burn: "Burn",
      cut: "Cut / Laceration",
    };
    return typeMap[woundType.toLowerCase()] || woundType;
  };

  return (
    <div className={styles.firstaidManagementPage}>
      <title>{t("title.admin_first_aid")}</title>
      <div className={styles.adminPageHeader}>
        <div className={styles.adminPageTitle}>
          <h1>{t("admin.first_aid.title")}</h1>
          <p>{t("admin.first_aid.subtitle")}</p>
        </div>
        <button className={styles.adminBtnPrimary} onClick={handleOpenAddModal}>
          <Plus size={20} />
          {t("admin.first_aid.add_guidance")}
        </button>
      </div>

      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={`${styles.statIcon} ${styles.statIconPrimary}`}>
            <BookOpen size={24} />
          </div>
          <div className={styles.statDetails}>
            <div className={styles.statValue}>{stats.total_guides}</div>
            <div className={styles.statLabel}>
              {t("admin.first_aid.total_guides")}
            </div>
          </div>
        </div>
        <div className={styles.statCard}>
          <div className={`${styles.statIcon} ${styles.statIconSuccess}`}>
            <Activity size={24} />
          </div>
          <div className={styles.statDetails}>
            <div className={styles.statValue}>{stats.active_guides}</div>
            <div className={styles.statLabel}>
              {t("admin.first_aid.active_guides")}
            </div>
          </div>
        </div>
        <div className={styles.statCard}>
          <div className={`${styles.statIcon} ${styles.statIconInfo}`}>
            <AlertCircle size={24} />
          </div>
          <div className={styles.statDetails}>
            <div className={styles.statValue}>{stats.wound_types}</div>
            <div className={styles.statLabel}>
              {t("admin.first_aid.wound_types")}
            </div>
          </div>
        </div>
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
        Total Guides ({totalCount} total)
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
                        {guide.wound_type.charAt(0).toUpperCase() +
                          guide.wound_type.slice(1)}
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
    </div>
  );
}
