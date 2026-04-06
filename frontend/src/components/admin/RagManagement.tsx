import { useState, useEffect, useRef } from 'react'
import { toast } from 'sonner'
import { Toaster } from 'sonner'
import { useTranslation } from 'react-i18next'
import {
  Upload, FileText, CheckCircle, Clock, AlertTriangle,
  Search, Eye, Trash2, X, AlertCircle,
  ChevronLeft, ChevronRight, Database,
} from 'lucide-react'
import * as ragService from '../../services/ragService'
import type { RagDocument } from '../../services/ragService'
import StatCard from './shared/StatCard'
import styles from './RagManagement.module.css'

// ── Helpers ────────────────────────────────────────────────

const STATUS_BADGE: Record<string, string> = {
  pending: styles.badgePending,
  indexing: styles.badgeIndexing,
  indexed: styles.badgeIndexed,
  failed: styles.badgeFailed,
}

const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// ── Main Component ─────────────────────────────────────────

export default function RagManagement() {
  const { t } = useTranslation()
  // Data
  const [documents, setDocuments] = useState<RagDocument[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10

  // Filters
  const [searchInput, setSearchInput] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [fileTypeFilter, setFileTypeFilter] = useState('all')
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Modals
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState<RagDocument | null>(null)

  // Upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadTags, setUploadTags] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [isDragActive, setIsDragActive] = useState(false)

  // Delete state
  const [isDeleting, setIsDeleting] = useState(false)

  // Stats (computed from full list or separate call)
  const [stats, setStats] = useState({ total: 0, indexed: 0, indexing: 0, failed: 0 })

  // ── Fetch Documents ──────────────────────────────────────

  const fetchDocuments = async () => {
    try {
      setLoading(true)
      const skip = (currentPage - 1) * itemsPerPage
      const res = await ragService.getRagDocuments({
        skip,
        limit: itemsPerPage,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        file_type: fileTypeFilter !== 'all' ? fileTypeFilter : undefined,
      })

      if (res.success && res.data) {
        setDocuments(res.data.items)
        setTotal(res.data.total)
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } }
      toast.error(error.response?.data?.message || 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  // Fetch stats (unfiltered count per status)
  const fetchStats = async () => {
    try {
      // Fetch all docs summary — we get total for each status
      const [allRes, indexedRes, indexingRes, failedRes] = await Promise.all([
        ragService.getRagDocuments({ limit: 1 }),
        ragService.getRagDocuments({ limit: 1, status: 'indexed' }),
        ragService.getRagDocuments({ limit: 1, status: 'indexing' }),
        ragService.getRagDocuments({ limit: 1, status: 'failed' }),
      ])

      setStats({
        total: allRes.data?.total ?? 0,
        indexed: indexedRes.data?.total ?? 0,
        indexing: indexingRes.data?.total ?? 0,
        failed: failedRes.data?.total ?? 0,
      })
    } catch {
      // Stats are non-critical
    }
  }

  useEffect(() => {
    fetchDocuments()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, searchTerm, statusFilter, fileTypeFilter])

  useEffect(() => {
    fetchStats()
  }, [])

  // Debounce search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setSearchTerm(searchInput)
      setCurrentPage(1)
    }, 400)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [searchInput])

  // ── Upload ───────────────────────────────────────────────

  const handleUpload = async () => {
    if (!uploadFile) return
    try {
      setIsUploading(true)
      const metadata = uploadTags.trim() ? uploadTags.trim() : undefined
      const res = await ragService.uploadRagDocument(uploadFile, metadata)
      if (res.success) {
        toast.success(`Uploaded "${res.data.file_name}" successfully. Indexing started.`)
        setShowUploadModal(false)
        resetUploadForm()
        fetchDocuments()
        fetchStats()
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } }
      toast.error(error.response?.data?.message || 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const resetUploadForm = () => {
    setUploadFile(null)
    setUploadTags('')
    setIsDragActive(false)
  }

  // Drag & Drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true)
    } else if (e.type === 'dragleave') {
      setIsDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setUploadFile(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadFile(e.target.files[0])
    }
  }

  // ── Delete ───────────────────────────────────────────────

  const handleDelete = async () => {
    if (!selectedDoc) return
    try {
      setIsDeleting(true)
      const res = await ragService.deleteRagDocument(selectedDoc.rag_document_id)
      if (res.success) {
        toast.success(`Deleted "${res.data.file_name}" and ${res.data.vectors_deleted} vectors`)
        setShowDeleteConfirm(false)
        setSelectedDoc(null)
        fetchDocuments()
        fetchStats()
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } }
      toast.error(error.response?.data?.message || 'Delete failed')
    } finally {
      setIsDeleting(false)
    }
  }

  // ── View Details ─────────────────────────────────────────

  const openDetails = (doc: RagDocument) => {
    setSelectedDoc(doc)
    setShowDetailsModal(true)
  }

  const openDeleteConfirm = (doc: RagDocument) => {
    setSelectedDoc(doc)
    setShowDeleteConfirm(true)
  }

  // ── Pagination ───────────────────────────────────────────

  const totalPages = Math.ceil(total / itemsPerPage)
  const startIdx = (currentPage - 1) * itemsPerPage + 1
  const endIdx = Math.min(currentPage * itemsPerPage, total)

  const getPageNumbers = () => {
    const pages: (number | string)[] = []
    const maxVisible = 5

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) pages.push(i)
    } else {
      pages.push(1)
      if (currentPage > 3) pages.push('...')

      const start = Math.max(2, currentPage - 1)
      const end = Math.min(totalPages - 1, currentPage + 1)
      for (let i = start; i <= end; i++) pages.push(i)

      if (currentPage < totalPages - 2) pages.push('...')
      pages.push(totalPages)
    }
    return pages
  }

  // Client-side search filtering (search is local since the API doesn't have search)
  const filteredDocs = searchTerm
    ? documents.filter((d) =>
        d.file_name.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : documents

  // ── Loading State ────────────────────────────────────────

  if (loading && documents.length === 0) {
    return (
      <div className={styles.ragManagementPage}>
        <div className={styles.loadingContainer}>
          <div className={styles.loadingSpinner} />
          <p className={styles.loadingText}>{t('admin.rag.loading')}</p>
        </div>
      </div>
    )
  }

  // ── Render ───────────────────────────────────────────────

  return (
    <div className={styles.ragManagementPage}>
      <Toaster richColors position="top-right" />

      {/* Header */}
      <div className={styles.pageHeader}>
        <div className={styles.pageTitle}>
          <h1>{t('admin.rag.title')}</h1>
          <p>{t('admin.rag.subtitle')}</p>
        </div>
        <button className={styles.btnPrimary} onClick={() => setShowUploadModal(true)}>
          <Upload size={18} />
          {t('admin.rag.upload_document')}
        </button>
      </div>

      {/* Stats Cards */}
      <div className={styles.statsGrid}>
        <StatCard
          icon={FileText}
          value={stats.total}
          label={t('admin.rag.total_documents')}
          color="default"
        />
        <StatCard
          icon={CheckCircle}
          value={stats.indexed}
          label={t('admin.rag.indexed_successfully')}
          color="green"
        />
        <StatCard
          icon={Clock}
          value={stats.indexing}
          label={t('admin.rag.indexing_in_progress')}
          color="yellow"
        />
        <StatCard
          icon={AlertTriangle}
          value={stats.failed}
          label={t('admin.rag.failed_to_index')}
          color="red"
        />
      </div>

      {/* Search & Filter */}
      <div className={styles.filtersCard}>
        <div className={styles.filterGroup}>
          <label>{t('admin.rag.filter_search')}</label>
          <div className={styles.searchBox}>
            <Search size={16} className={styles.searchIcon} />
            <input
              className={styles.searchInput}
              placeholder={t('admin.rag.search_placeholder')}
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>
        </div>
        <div className={styles.filterGroup}>
          <label>{t('admin.rag.filter_status')}</label>
          <select
            className={styles.filterSelect}
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1) }}
          >
            <option value="all">{t('admin.rag.status_all')}</option>
            <option value="pending">{t('admin.rag.status_pending')}</option>
            <option value="indexing">{t('admin.rag.status_indexing')}</option>
            <option value="indexed">{t('admin.rag.status_indexed')}</option>
            <option value="failed">{t('admin.rag.status_failed')}</option>
          </select>
        </div>
        <div className={styles.filterGroup}>
          <label>{t('admin.rag.filter_type')}</label>
          <select
            className={styles.filterSelect}
            value={fileTypeFilter}
            onChange={(e) => { setFileTypeFilter(e.target.value); setCurrentPage(1) }}
          >
            <option value="all">{t('admin.rag.type_all')}</option>
            <option value="pdf">PDF</option>
            <option value="md">MD</option>
            <option value="txt">TXT</option>
            <option value="docx">DOCX</option>
            <option value="html">HTML</option>
            <option value="csv">CSV</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className={styles.tableCard}>
        <div className={styles.tableWrapper}>
          <table className={styles.docTable}>
            <thead>
              <tr>
                <th>File Name</th>
                <th>File Type</th>
                <th>Status</th>
                <th>Chunks</th>
                <th>Upload Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={6}>
                    <div className={styles.emptyState}>
                      <Database size={48} />
                      <p>No documents found</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredDocs.map((doc) => (
                  <tr key={doc.rag_document_id}>
                    <td>
                      <div className={styles.fileNameCell}>
                        <div className={styles.fileIcon}>
                          <FileText size={16} />
                        </div>
                        <span className={styles.fileName}>{doc.file_name}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`${styles.badge} ${styles.badgeFileType}`}>
                        {doc.file_type.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <span className={`${styles.badge} ${STATUS_BADGE[doc.status] || ''}`}>
                        {capitalize(doc.status)}
                      </span>
                    </td>
                    <td>{doc.chunk_count}</td>
                    <td>{formatDate(doc.created_at)}</td>
                    <td className={styles.actionsCell}>
                      <button
                        className={`${styles.btnIcon} ${styles.btnView}`}
                        title="View Details"
                        onClick={() => openDetails(doc)}
                      >
                        <Eye size={16} />
                      </button>
                      <button
                        className={`${styles.btnIcon} ${styles.btnDelete}`}
                        title="Delete"
                        onClick={() => openDeleteConfirm(doc)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {total > 0 && (
          <div className={styles.paginationBar}>
            <span className={styles.paginationInfo}>
              Showing {startIdx} to {endIdx} of {total} documents
            </span>
            {totalPages > 1 && (
              <div className={styles.paginationControls}>
                <button
                  className={styles.paginationBtn}
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                >
                  <ChevronLeft size={14} /> Prev
                </button>
                {getPageNumbers().map((page, idx) =>
                  typeof page === 'string' ? (
                    <span key={`ellipsis-${idx}`} style={{ color: '#94a3b8', padding: '0 0.25rem' }}>
                      …
                    </span>
                  ) : (
                    <button
                      key={page}
                      className={`${styles.pageNumber} ${
                        currentPage === page ? styles.pageNumberActive : ''
                      }`}
                      onClick={() => setCurrentPage(page)}
                    >
                      {page}
                    </button>
                  )
                )}
                <button
                  className={styles.paginationBtn}
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                >
                  Next <ChevronRight size={14} />
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ═══ Upload Modal ═══ */}
      {showUploadModal && (
        <div className={styles.modalOverlay} onClick={() => !isUploading && setShowUploadModal(false)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div>
                <h2>Upload Medical Document</h2>
                <p className={styles.modalSubtitle}>Upload documents to add them to the knowledge base</p>
              </div>
              <button className={styles.modalClose} onClick={() => !isUploading && setShowUploadModal(false)}>
                <X size={20} />
              </button>
            </div>

            <div className={styles.modalBody}>
              {/* Drop Zone */}
              <div
                className={`${styles.dropZone} ${isDragActive ? styles.dropZoneActive : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => document.getElementById('rag-file-input')?.click()}
              >
                <div className={styles.dropZoneIconWrap}>
                  <Upload size={24} />
                </div>
                <p className={styles.dropZoneText}>
                  {isDragActive ? 'Drop your file here' : 'Drag and drop your file here'}
                </p>
                <p className={styles.dropZoneHint}>or click to browse from your computer</p>
                <p className={styles.dropZoneHint}>
                  Allowed: .pdf, .md, .txt, .docx, .html, .csv (Max 50MB)
                </p>
                <input
                  id="rag-file-input"
                  type="file"
                  accept=".pdf,.md,.txt,.docx,.html,.csv"
                  onChange={handleFileInput}
                  style={{ display: 'none' }}
                />
              </div>

              {/* File Preview */}
              {uploadFile && (
                <div className={styles.filePreview}>
                  <div className={styles.filePreviewInfo}>
                    <p className={styles.filePreviewName}>{uploadFile.name}</p>
                    <p className={styles.filePreviewSize}>{formatFileSize(uploadFile.size)}</p>
                  </div>
                  <button className={styles.btnRemoveFile} onClick={() => setUploadFile(null)}>
                    <X size={16} />
                  </button>
                </div>
              )}

              {/* Metadata */}
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Metadata / Tags (Optional)</label>
                <input
                  className={styles.formInput}
                  placeholder='e.g., {"topic": "burns", "source": "WHO"}'
                  value={uploadTags}
                  onChange={(e) => setUploadTags(e.target.value)}
                />
              </div>
            </div>

            <div className={styles.modalFooter}>
              <button
                className={styles.btnCancel}
                onClick={() => { setShowUploadModal(false); resetUploadForm() }}
                disabled={isUploading}
              >
                Cancel
              </button>
              <button
                className={styles.btnSubmit}
                onClick={handleUpload}
                disabled={!uploadFile || isUploading}
              >
                {isUploading ? (
                  <>
                    <span className={styles.spinnerInline} />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload size={16} />
                    Upload
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ Details Modal ═══ */}
      {showDetailsModal && selectedDoc && (
        <div className={styles.modalOverlay} onClick={() => setShowDetailsModal(false)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div>
                <h2>Document Details</h2>
                <p className={styles.modalSubtitle}>Detailed information about this document</p>
              </div>
              <button className={styles.modalClose} onClick={() => setShowDetailsModal(false)}>
                <X size={20} />
              </button>
            </div>

            <div className={styles.modalBody}>
              {/* File Name Header */}
              <div className={styles.fileNameCell} style={{ marginBottom: '1.25rem' }}>
                <div className={styles.fileIcon}>
                  <FileText size={16} />
                </div>
                <span className={styles.fileName} style={{ fontSize: '1.125rem' }}>
                  {selectedDoc.file_name}
                </span>
              </div>

              {/* Metadata Grid */}
              <div className={styles.detailGrid}>
                <div className={styles.detailItem}>
                  <p className={styles.detailLabel}>Document ID</p>
                  <p className={`${styles.detailValue} ${styles.detailValueMono}`}>
                    {selectedDoc.rag_document_id}
                  </p>
                </div>
                <div className={styles.detailItem}>
                  <p className={styles.detailLabel}>File Type</p>
                  <p className={styles.detailValue}>{selectedDoc.file_type.toUpperCase()}</p>
                </div>
                <div className={styles.detailItem}>
                  <p className={styles.detailLabel}>Status</p>
                  <span className={`${styles.badge} ${STATUS_BADGE[selectedDoc.status] || ''}`}>
                    {capitalize(selectedDoc.status)}
                  </span>
                </div>
                <div className={styles.detailItem}>
                  <p className={styles.detailLabel}>Chunks Generated</p>
                  <p className={styles.detailValue}>{selectedDoc.chunk_count}</p>
                </div>
                <div className={styles.detailItem}>
                  <p className={styles.detailLabel}>Created</p>
                  <p className={styles.detailValue}>{formatDate(selectedDoc.created_at)}</p>
                </div>
                <div className={styles.detailItem}>
                  <p className={styles.detailLabel}>Updated</p>
                  <p className={styles.detailValue}>{formatDate(selectedDoc.updated_at)}</p>
                </div>
              </div>

              {/* Error Box */}
              {selectedDoc.status === 'failed' && selectedDoc.error_message && (
                <div className={styles.errorBox}>
                  <div className={styles.errorBoxHeader}>
                    <AlertCircle size={18} />
                    Indexing Failed
                  </div>
                  <p className={styles.errorBoxText}>{selectedDoc.error_message}</p>
                </div>
              )}

              {/* Metadata */}
              {selectedDoc.doc_metadata && Object.keys(selectedDoc.doc_metadata).length > 0 && (
                <div className={styles.metadataBox}>
                  <p className={styles.detailLabel}>Metadata</p>
                  <pre>{JSON.stringify(selectedDoc.doc_metadata, null, 2)}</pre>
                </div>
              )}
            </div>

            <div className={styles.modalFooter}>
              <button className={styles.btnCancel} onClick={() => setShowDetailsModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ Delete Confirmation ═══ */}
      {showDeleteConfirm && selectedDoc && (
        <div className={styles.modalOverlay} onClick={() => !isDeleting && setShowDeleteConfirm(false)}>
          <div
            className={`${styles.modalContent} ${styles.confirmContent}`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className={styles.modalBody}>
              <h3 className={styles.confirmTitle}>Delete Document</h3>
              <p className={styles.confirmMessage}>
                Are you sure you want to delete <strong>"{selectedDoc.file_name}"</strong>?
                This will permanently remove the document and all its indexed vectors from the knowledge base.
                This action cannot be undone.
              </p>
            </div>
            <div className={styles.modalFooter}>
              <button
                className={styles.btnCancel}
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button className={styles.btnDanger} onClick={handleDelete} disabled={isDeleting}>
                {isDeleting ? (
                  <>
                    <span className={styles.spinnerInline} />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 size={16} />
                    Delete
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
