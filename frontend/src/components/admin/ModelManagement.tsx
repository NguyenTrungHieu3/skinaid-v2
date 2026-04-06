import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { Toaster } from 'sonner'
import {
  Upload, RotateCcw, ChevronDown, Eye, Trash2, CheckCircle2,
  Database, Activity, FileText, AlertCircle, Calendar, Play, Pause, X
} from 'lucide-react'
import * as modelService from '../../services/modelManagementService'
import type { AIModel } from '../../types/admin'
import StatCard from './shared/StatCard'
import styles from './ModelManagement.module.css'

// Grouped model data structure
interface ModelTypeGroup {
  modelType: string
  activeVersion: string | null
  versions: AIModel[]
  uploadDate: string
}

export default function ModelManagement() {
  const { t } = useTranslation()
  const [models, setModels] = useState<AIModel[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedModel, setSelectedModel] = useState<AIModel | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [uploadModelType, setUploadModelType] = useState<string>('detection')
  const [filterType, setFilterType] = useState<string>('all')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set())
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  // Confirmation dialog states
  const [deleteConfirm, setDeleteConfirm] = useState<{ open: boolean; modelId: string | null }>({ open: false, modelId: null })
  const [rollbackConfirm, setRollbackConfirm] = useState<{ open: boolean; modelType: string | null }>({ open: false, modelType: null })

  // Upload form state
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadVersionTag, setUploadVersionTag] = useState('v1.0.0')
  const [uploadDescription, setUploadDescription] = useState('')

  useEffect(() => {
    loadModels()
  }, [filterType, filterStatus])

  const loadModels = async () => {
    try {
      setLoading(true)
      const modelType = filterType === 'all' ? undefined : filterType
      const result = await modelService.listModels(modelType, filterStatus)
      if (result.success && result.data) {
        setModels(result.data.models)
      }
    } catch (err: any) {
      toast.error(err.message || t('admin.model_management.loading'))
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async () => {
    if (!uploadFile) {
      toast.error('Please select a file')
      return
    }
    try {
      setUploading(true)
      await modelService.uploadModel(
        uploadFile,
        {
          model_type: uploadModelType,
          version_tag: uploadVersionTag,
          description: uploadDescription || undefined,
          is_beta: false,
        },
        (progress) => setUploadProgress(progress)
      )
      toast.success(t('admin.model_management.upload_modal.upload_success'))
      setShowUploadModal(false)
      resetUploadForm()
      loadModels()
    } catch (err: any) {
      toast.error(err.message || t('admin.model_management.upload_modal.upload_failed'))
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const resetUploadForm = () => {
    setUploadFile(null)
    setUploadVersionTag('v1.0.0')
    setUploadDescription('')
    setUploadProgress(0)
  }

  const handleActivate = async (modelId: string) => {
    try {
      const result = await modelService.activateModel(modelId)
      if (result.success) {
        toast.success(t('admin.model_management.messages.activate_success'))
        loadModels()
      }
    } catch (err: any) {
      toast.error(err.message || t('admin.model_management.messages.error'))
    }
  }

  const handleRollback = async (modelType: string) => {
    try {
      const result = await modelService.rollbackModel(modelType)
      if (result.success) {
        toast.success(t('admin.model_management.messages.rollback_success'))
        loadModels()
      }
    } catch (err: any) {
      toast.error(err.message || t('admin.model_management.messages.error'))
    }
  }

  const handleDelete = async (modelId: string) => {
    try {
      const result = await modelService.deleteModel(modelId)
      if (result.success) {
        toast.success(t('admin.model_management.messages.delete_success'))
        loadModels()
      }
    } catch (err: any) {
      toast.error(err.message || t('admin.model_management.messages.error'))
    }
  }

  const handleDeactivate = async (modelId: string) => {
    try {
      const result = await modelService.deactivateModel(modelId)
      if (result.success) {
        toast.success(t('admin.model_management.messages.deactivate_success'))
        loadModels()
      }
    } catch (err: any) {
      toast.error(err.message || t('admin.model_management.messages.error'))
    }
  }

  const handleViewDetails = (model: AIModel) => {
    setSelectedModel(model)
    setShowDetailModal(true)
  }

  const toggleExpanded = (modelType: string) => {
    const newExpanded = new Set(expandedTypes)
    if (newExpanded.has(modelType)) {
      newExpanded.delete(modelType)
    } else {
      newExpanded.add(modelType)
    }
    setExpandedTypes(newExpanded)
  }

  // Group models by type
  const groupedModels = models.reduce((acc, model) => {
    if (!acc[model.model_type]) {
      acc[model.model_type] = {
        modelType: model.model_type,
        activeVersion: model.is_active ? model.version_tag || null : null,
        versions: [],
        uploadDate: model.created_at,
      }
    }
    acc[model.model_type].versions.push(model)
    if (model.is_active) {
      acc[model.model_type].activeVersion = model.version_tag || null
      acc[model.model_type].uploadDate = model.created_at
    }
    return acc
  }, {} as Record<string, ModelTypeGroup>)

  const typesWithoutActive = Object.values(groupedModels).filter((g) => !g.activeVersion)

  const getModelTypeIcon = (type: string) => {
    switch (type) {
      case 'detection': return <Activity size={16} />
      case 'classification': return <FileText size={16} />
      case 'segmentation': return <Database size={16} />
      default: return <Database size={16} />
    }
  }

  const filteredGroups = Object.values(groupedModels).filter((group) => {
    if (searchTerm && !group.modelType.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  const totalModels = Object.keys(groupedModels).length
  const activeVersions = Object.values(groupedModels).filter((g) => g.activeVersion).length
  const totalVersions = models.length

  // --- LOADING ---
  if (loading) {
    return (
      <div className={styles.modelManagementPage}>
        <div className={styles.loadingContainer}>
          <div className={styles.loadingSpinner}></div>
          <p className={styles.loadingText}>{t('admin.model_management.loading')}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.modelManagementPage}>
      <Toaster richColors position="top-right" />

      {/* Header */}
      <div className={styles.pageHeader}>
        <div className={styles.pageTitle}>
          <h1>{t('admin.model_management.title')}</h1>
          <p>{t('admin.model_management.subtitle')}</p>
        </div>
        <button className={styles.btnPrimary} onClick={() => setShowUploadModal(true)}>
          <Upload size={18} />
          {t('admin.model_management.upload_model')}
        </button>
      </div>

      {/* Stats */}
      <div className={styles.statsGrid}>
        <StatCard
          icon={Database}
          value={totalModels}
          label={t('admin.model_management.total_models')}
          color="default"
        />
        <StatCard
          icon={CheckCircle2}
          value={activeVersions}
          label={t('admin.model_management.active_version')}
          color="green"
        />
        <StatCard
          icon={FileText}
          value={totalVersions}
          label={t('admin.model_management.total_versions')}
          color="blue"
        />
      </div>

      {/* Warning */}
      {typesWithoutActive.length > 0 && (
        <div className={styles.warningBanner}>
          <AlertCircle size={20} className={styles.warningIcon} />
          <div>
            <p className={styles.warningTitle}>{t('admin.model_management.no_active_warning_title')}</p>
            <p className={styles.warningText}>
              {t('admin.model_management.no_active_warning', {
                types: typesWithoutActive.map((g) => g.modelType).join(', ')
              })}
            </p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className={styles.filtersCard}>
        <div className={styles.filterGroup}>
          <label>{t('admin.model_management.filters.model_type')}</label>
          <select className={styles.filterSelect} value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            <option value="all">{t('admin.model_management.filters.all_types')}</option>
            <option value="detection">{t('admin.model_management.filters.detection')}</option>
            <option value="classification">{t('admin.model_management.filters.classification')}</option>
            <option value="segmentation">{t('admin.model_management.filters.segmentation')}</option>
            <option value="severity_scoring">{t('admin.model_management.filters.severity_scoring')}</option>
          </select>
        </div>
        <div className={styles.filterGroup}>
          <label>{t('admin.model_management.filters.status')}</label>
          <select className={styles.filterSelect} value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="all">{t('admin.model_management.filters.all')}</option>
            <option value="active">{t('admin.model_management.filters.active')}</option>
            <option value="inactive">{t('admin.model_management.filters.inactive')}</option>
          </select>
        </div>
        <div className={styles.filterGroup}>
          <label>{t('admin.model_management.filters.search')}</label>
          <input
            className={styles.filterInput}
            placeholder={t('admin.model_management.filters.search_placeholder')}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Model Groups */}
      {filteredGroups.length === 0 ? (
        <div className={styles.emptyState}>
          <Database size={64} />
          <p>{t('admin.model_management.no_models')}</p>
        </div>
      ) : (
        filteredGroups.map((group) => (
          <div key={group.modelType} className={styles.modelGroupSection}>
            <div className={styles.modelGroupTitle}>
              {getModelTypeIcon(group.modelType)}
              <span>{group.modelType}</span>
              {group.activeVersion && (
                <span className={styles.activeBadge}>
                  <CheckCircle2 size={12} />
                  {group.activeVersion}
                </span>
              )}
            </div>

            <div className={styles.accordionCard}>
              <button className={styles.accordionHeader} onClick={() => toggleExpanded(group.modelType)}>
                <div className={styles.accordionHeaderLeft}>
                  <ChevronDown size={20} className={`${styles.chevronIcon} ${expandedTypes.has(group.modelType) ? styles.expanded : ''}`} />
                  <div className={styles.accordionHeaderInfo}>
                    <h3>{group.modelType}</h3>
                    <p>{group.versions.length} {group.versions.length === 1 ? t('admin.model_management.version') : t('admin.model_management.versions')}</p>
                  </div>
                </div>
                <div className={styles.accordionHeaderRight}>
                  <span className={styles.dateInfo}>
                    <Calendar size={14} />
                    {new Date(group.uploadDate).toLocaleDateString()}
                  </span>
                  {group.activeVersion ? (
                    <span className={styles.activeBadge}>
                      <CheckCircle2 size={12} />
                      {group.activeVersion}
                    </span>
                  ) : (
                    <span className={styles.noActiveBadge}>{t('admin.model_management.no_active_version')}</span>
                  )}
                </div>
              </button>

              {expandedTypes.has(group.modelType) && (
                <div className={styles.accordionContent}>
                  <div className={styles.accordionActions}>
                    <button
                      className={styles.btnUploadVersion}
                      onClick={() => { setUploadModelType(group.modelType); setShowUploadModal(true) }}
                    >
                      <Upload size={14} />
                      {t('admin.model_management.actions.upload_new_version')}
                    </button>
                    {group.activeVersion && group.versions.length > 1 && (
                      <button
                        className={styles.btnRollback}
                        onClick={() => setRollbackConfirm({ open: true, modelType: group.modelType })}
                      >
                        <RotateCcw size={14} />
                        {t('admin.model_management.rollback')}
                      </button>
                    )}
                  </div>

                  <div className={styles.versionList}>
                    {group.versions.map((version) => (
                      <div key={version.model_id} className={styles.versionRow}>
                        <div className={styles.versionInfo}>
                          <span className={`${styles.versionTag} ${version.is_active ? styles.active : styles.inactive}`}>
                            {version.version_tag}
                          </span>
                          <div>
                            <div className={`${styles.versionStatus} ${version.is_active ? styles.active : styles.inactive}`}>
                              {version.is_active && <CheckCircle2 size={12} />}
                              {version.is_active ? t('admin.model_management.filters.active') : t('admin.model_management.filters.inactive')}
                            </div>
                            <div className={styles.versionDate}>
                              {new Date(version.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>

                        <div className={styles.versionActions}>
                          {!version.is_active && (
                            <button className={`${styles.btnAction} ${styles.btnActivate}`} onClick={() => handleActivate(version.model_id)}>
                              <Play size={14} /> {t('admin.model_management.activate')}
                            </button>
                          )}
                          {version.is_active && (
                            <button className={`${styles.btnAction} ${styles.btnDeactivate}`} onClick={() => handleDeactivate(version.model_id)}>
                              <Pause size={14} /> {t('admin.model_management.deactivate')}
                            </button>
                          )}
                          <button className={`${styles.btnAction} ${styles.btnView}`} onClick={() => handleViewDetails(version)}>
                            <Eye size={14} />
                          </button>
                          <button
                            className={`${styles.btnAction} ${styles.btnDelete}`}
                            onClick={() => setDeleteConfirm({ open: true, modelId: version.model_id })}
                            disabled={version.is_active}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className={styles.modalOverlay} onClick={() => !uploading && setShowUploadModal(false)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>{t('admin.model_management.upload_modal.title')}</h2>
              <button className={styles.modalClose} onClick={() => !uploading && setShowUploadModal(false)}>
                <X size={20} />
              </button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.formGroup}>
                <label>{t('admin.model_management.upload_modal.model_type_label')}</label>
                <select className={styles.formInput} value={uploadModelType} onChange={(e) => setUploadModelType(e.target.value)}>
                  <option value="detection">{t('admin.model_management.filters.detection')}</option>
                  <option value="classification">{t('admin.model_management.filters.classification')}</option>
                  <option value="segmentation">{t('admin.model_management.filters.segmentation')}</option>
                  <option value="severity_scoring">{t('admin.model_management.filters.severity_scoring')}</option>
                </select>
              </div>
              <div className={styles.formGroup}>
                <label>{t('admin.model_management.upload_modal.version_tag_label')}</label>
                <input className={styles.formInput} value={uploadVersionTag} onChange={(e) => setUploadVersionTag(e.target.value)} placeholder="v1.0.0" />
              </div>
              <div className={styles.formGroup}>
                <label>{t('admin.model_management.upload_modal.description_label')}</label>
                <textarea className={styles.formTextarea} value={uploadDescription} onChange={(e) => setUploadDescription(e.target.value)} rows={3} placeholder="Describe your model..." />
              </div>
              <div className={styles.formGroup}>
                <label>{t('admin.model_management.upload_modal.select_file')}</label>
                <label className={styles.dropZone} htmlFor="file-upload">
                  <input type="file" accept=".pt,.pth,.h5,.onnx,.safetensors" onChange={(e) => setUploadFile(e.target.files?.[0] || null)} style={{ display: 'none' }} id="file-upload" />
                  <Upload size={40} className={styles.dropZoneIcon} />
                  <p className={styles.dropZoneText}>{uploadFile ? uploadFile.name : t('admin.model_management.upload_modal.drag_drop')}</p>
                  <p className={styles.dropZoneHint}>{t('admin.model_management.upload_modal.file_types')}</p>
                  <p className={styles.dropZoneHint}>{t('admin.model_management.upload_modal.max_size')}</p>
                </label>
              </div>
              {uploading && (
                <div>
                  <div className={styles.progressBar}>
                    <div className={styles.progressFill} style={{ width: `${uploadProgress}%` }} />
                  </div>
                  <p className={styles.progressText}>{uploadProgress}%</p>
                </div>
              )}
            </div>
            <div className={styles.modalFooter}>
              <button className={styles.btnCancel} onClick={() => setShowUploadModal(false)} disabled={uploading}>{t('button.cancel')}</button>
              <button className={styles.btnSubmit} onClick={handleUpload} disabled={uploading || !uploadFile}>
                {uploading ? (<><span className={styles.spinnerInline}></span> {t('admin.model_management.upload_modal.uploading')}</>) : (<><Upload size={16} /> {t('admin.model_management.upload_model')}</>)}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {selectedModel && showDetailModal && (
        <div className={styles.modalOverlay} onClick={() => setShowDetailModal(false)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>{t('admin.model_management.view_details')}</h2>
              <button className={styles.modalClose} onClick={() => setShowDetailModal(false)}>
                <X size={20} />
              </button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.detailGrid}>
                <div className={styles.detailItem}>
                  <p className={styles.label}>{t('admin.model_management.model_type')}</p>
                  <p className={styles.value}>{selectedModel.model_type}</p>
                </div>
                <div className={styles.detailItem}>
                  <p className={styles.label}>{t('admin.model_management.active_version')}</p>
                  <p className={styles.value}>{selectedModel.current_version || t('admin.model_management.none')}</p>
                </div>
                <div className={styles.detailItem}>
                  <p className={styles.label}>{t('admin.model_management.total_versions')}</p>
                  <p className={styles.value}>{selectedModel.total_versions}</p>
                </div>
                <div className={styles.detailItem}>
                  <p className={styles.label}>{t('admin.model_management.upload_date')}</p>
                  <p className={styles.value}>{new Date(selectedModel.created_at).toLocaleDateString()}</p>
                </div>
              </div>
              {selectedModel.metrics && (
                <div className={styles.metricsSection}>
                  <h3>{t('admin.model_management.metrics')}</h3>
                  <div className={styles.metricsGrid}>
                    {selectedModel.metrics.accuracy && (
                      <div className={`${styles.metricCard} ${styles.accuracy}`}>
                        <p className={styles.metricLabel}>Accuracy</p>
                        <p className={styles.metricValue}>{(selectedModel.metrics.accuracy * 100).toFixed(1)}%</p>
                      </div>
                    )}
                    {selectedModel.metrics.precision && (
                      <div className={`${styles.metricCard} ${styles.precision}`}>
                        <p className={styles.metricLabel}>Precision</p>
                        <p className={styles.metricValue}>{(selectedModel.metrics.precision * 100).toFixed(1)}%</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
            <div className={styles.modalFooter}>
              <button className={styles.btnCancel} onClick={() => setShowDetailModal(false)}>{t('button.cancel')}</button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {deleteConfirm.open && (
        <div className={styles.modalOverlay} onClick={() => setDeleteConfirm({ open: false, modelId: null })}>
          <div className={`${styles.modalContent} ${styles.confirmContent}`} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalBody}>
              <h3 className={styles.confirmTitle}>{t('admin.model_management.confirm.delete_title')}</h3>
              <p className={styles.confirmMessage}>{t('admin.model_management.confirm.delete_message')}</p>
            </div>
            <div className={styles.modalFooter}>
              <button className={styles.btnCancel} onClick={() => setDeleteConfirm({ open: false, modelId: null })}>{t('button.cancel')}</button>
              <button className={styles.btnDanger} onClick={() => { if (deleteConfirm.modelId) handleDelete(deleteConfirm.modelId); setDeleteConfirm({ open: false, modelId: null }) }}>
                {t('admin.model_management.confirm.yes')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rollback Confirmation */}
      {rollbackConfirm.open && (
        <div className={styles.modalOverlay} onClick={() => setRollbackConfirm({ open: false, modelType: null })}>
          <div className={`${styles.modalContent} ${styles.confirmContent}`} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalBody}>
              <h3 className={styles.confirmTitle}>{t('admin.model_management.confirm.rollback_title')}</h3>
              <p className={styles.confirmMessage}>{t('admin.model_management.confirm.rollback_message')}</p>
            </div>
            <div className={styles.modalFooter}>
              <button className={styles.btnCancel} onClick={() => setRollbackConfirm({ open: false, modelType: null })}>{t('button.cancel')}</button>
              <button className={styles.btnConfirmPrimary} onClick={() => { if (rollbackConfirm.modelType) handleRollback(rollbackConfirm.modelType); setRollbackConfirm({ open: false, modelType: null }) }}>
                {t('admin.model_management.confirm.yes')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
