import { useState, useEffect, useRef, useMemo } from 'react';
import { toast, Toaster } from 'sonner';
import {
  Bell, BellOff, Send, Search, Trash2, Eye,
  ChevronLeft, ChevronRight, X, Loader2, Plus,
  AlertCircle, Users, Megaphone, CheckCircle, Check,
  Settings, Info, AlertTriangle, Gift, Activity, type LucideIcon,
} from 'lucide-react';
import * as notificationService from '../../services/notificationService';
import type { NotificationItem, CreateNotificationPayload, BroadcastResult } from '../../services/notificationService';

import { getUsers } from '../../services/userService';
import type { UserListItem } from '../../services/userService';
import StatCard from './shared/StatCard';
import styles from './NotificationManagement.module.css';

// ── Helpers ────────────────────────────────────────────────

const NOTIF_TYPE_OPTIONS = [
  { value: 'system', label: 'Hệ thống' },
  { value: 'admin', label: 'Quản trị' },
  { value: 'info', label: 'Thông tin' },
  { value: 'warning', label: 'Cảnh báo' },
  { value: 'promotion', label: 'Khuyến mãi' },
];

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Thấp' },
  { value: 'normal', label: 'Bình thường' },
  { value: 'high', label: 'Cao' },
];

const TYPE_DISPLAY: Record<string, { label: string; Icon: LucideIcon; color: string; className: string }> = {
  analysis_complete: { label: 'Phân tích', Icon: Activity, color: '#6366f1', className: 'typeAnalysis' },
  system:           { label: 'Hệ thống', Icon: Settings, color: '#64748b', className: 'typeSystem' },
  admin:            { label: 'Quản trị', Icon: Bell, color: '#0ea5e9', className: 'typeAdmin' },
  info:             { label: 'Thông tin', Icon: Info, color: '#3b82f6', className: 'typeInfo' },
  warning:          { label: 'Cảnh báo', Icon: AlertTriangle, color: '#f59e0b', className: 'typeWarning' },
  promotion:        { label: 'Khuyến mãi', Icon: Gift, color: '#ec4899', className: 'typePromotion' },
};

const PRIORITY_DISPLAY: Record<string, { label: string; className: string }> = {
  low: { label: 'Thấp', className: 'priorityLow' },
  normal: { label: 'Bình thường', className: 'priorityNormal' },
  high: { label: 'Cao', className: 'priorityHigh' },
};

const formatDateTime = (iso: string) => {
  const d = iso.endsWith('Z') ? iso : `${iso}Z`;
  return new Date(d).toLocaleString('vi-VN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const getRelativeTime = (dateStr: string) => {
  const d = dateStr.endsWith('Z') ? dateStr : `${dateStr}Z`;
  const ms = Date.now() - new Date(d).getTime();
  const sec = Math.floor(ms / 1000);
  if (sec < 60) return 'Vừa xong';
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} phút trước`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} giờ trước`;
  const day = Math.floor(hr / 24);
  if (day < 30) return `${day} ngày trước`;
  return new Date(d).toLocaleDateString('vi-VN');
};

// ── Component ─────────────────────────────────────────────

interface NotificationManagementProps {
  onNavigate?: (page: string) => void;
}

export default function NotificationManagement({ onNavigate }: NotificationManagementProps) {
  // Data
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Filters
  const [searchInput, setSearchInput] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Create modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  // recipient type: 'specific' | 'all'
  const [recipientType, setRecipientType] = useState<'specific' | 'all'>('specific');
  const [userSearchInput, setUserSearchInput] = useState('');
  const [userSearchResults, setUserSearchResults] = useState<UserListItem[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserListItem | null>(null);
  const userDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [createForm, setCreateForm] = useState({
    title: '',
    body: '',
    notification_type: 'system',
    priority: 'normal',
    action_url: '',
  });

  // Detail / Delete
  const [selectedNotif, setSelectedNotif] = useState<NotificationItem | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<NotificationItem | null>(null);
  const [deleting, setDeleting] = useState(false);

  // ── Fetch ─────────────────────────────────────────────────

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const skip = (currentPage - 1) * itemsPerPage;
      const data = await notificationService.getAllNotifications({
        skip,
        limit: itemsPerPage,
        notification_type: typeFilter !== 'all' ? typeFilter : undefined,
      });
      setNotifications(data.items);
      setTotal(data.total);
    } catch {
      toast.error('Không thể tải danh sách thông báo');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, typeFilter, priorityFilter, searchTerm]);

  // Debounce search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setSearchTerm(searchInput);
      setCurrentPage(1);
    }, 400);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [searchInput]);

  // Client-side search + priority filter
  const filteredNotifs = notifications.filter(n => {
    const matchSearch = !searchTerm ||
      n.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      n.body.toLowerCase().includes(searchTerm.toLowerCase());
    const matchPriority = priorityFilter === 'all' || n.priority === priorityFilter;
    return matchSearch && matchPriority;
  });

  // Deduplicate for admin view: Group broadcast notifications together
  const deduplicatedNotifs = useMemo(() => {
    const grouped: NotificationItem[] = [];
    
    for (const notif of filteredNotifs) {
      // Find an existing notification that looks identical (same title, body, type, and created within 10 seconds of each other)
      const isDuplicate = grouped.find(g => 
        g.title === notif.title && 
        g.body === notif.body && 
        g.notification_type === notif.notification_type &&
        Math.abs(new Date(g.created_at).getTime() - new Date(notif.created_at).getTime()) < 10000
      );

      if (isDuplicate) {
        // Tag the existing item as a broadcast so we can display a badge
        (isDuplicate as NotificationItem & { isBroadcast?: boolean; broadcastCount?: number }).isBroadcast = true;
        (isDuplicate as NotificationItem & { broadcastCount?: number }).broadcastCount = ((isDuplicate as NotificationItem & { broadcastCount?: number }).broadcastCount || 1) + 1;
      } else {
        grouped.push({ ...notif }); // copy so we can safely mutate
      }
    }
    return grouped;
  }, [filteredNotifs]);

  // ── Read All / Mark as read ────────────────────────────────────────────────
  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllRead();
      toast.success('Đã đánh dấu tất cả là đã đọc');
      fetchNotifications();
    } catch {
      toast.error('Đánh dấu thất bại');
    }
  };

  const handleViewDetail = (notif: NotificationItem) => {
    if (onNavigate) {
      onNavigate(`notification_detail_${notif.notification_id}`);
    } else {
      setSelectedNotif(notif);
      setShowDetail(true);
    }
  };

  const confirmDelete = (notif: NotificationItem) => {
    setDeleteTarget(notif);
    setShowDeleteConfirm(true);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      setDeleting(true);
      await notificationService.deleteNotification(deleteTarget.notification_id);
      toast.success('Đã xóa thông báo');
      setShowDeleteConfirm(false);
      setDeleteTarget(null);
      fetchNotifications();
    } catch {
      toast.error('Không thể xóa thông báo');
    } finally {
      setDeleting(false);
    }
  };

  // ── Create ────────────────────────────────────────────────

  const searchUsers = async (query: string) => {
    if (!query.trim()) { setUserSearchResults([]); return; }
    try {
      setLoadingUsers(true);
      const data = await getUsers({ search: query, page: 1, page_size: 5 });
      setUserSearchResults(data.items);
    } catch {
      // silent
    } finally {
      setLoadingUsers(false);
    }
  };

  useEffect(() => {
    if (userDebounceRef.current) clearTimeout(userDebounceRef.current);
    userDebounceRef.current = setTimeout(() => {
      searchUsers(userSearchInput);
    }, 300);
    return () => { if (userDebounceRef.current) clearTimeout(userDebounceRef.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userSearchInput]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (recipientType === 'specific' && !selectedUser) {
      toast.error('Vui lòng chọn người nhận');
      return;
    }
    if (!createForm.title.trim() || !createForm.body.trim()) {
      toast.error('Vui lòng nhập tiêu đề và nội dung');
      return;
    }
    try {
      setCreating(true);
      const payload: CreateNotificationPayload = {
        recipient_type: recipientType,
        title: createForm.title.trim(),
        body: createForm.body.trim(),
        notification_type: createForm.notification_type,
        priority: createForm.priority,
        action_url: createForm.action_url.trim() || undefined,
        ...(recipientType === 'specific' && selectedUser ? { user_id: selectedUser.id } : {}),
      };

      const raw = await notificationService.createNotification(payload);

      if (recipientType === 'all') {
        const result = raw as unknown as BroadcastResult;
        toast.success(`Đã broadcast đến ${result.sent_count} người dùng`);
      } else {
        toast.success(`Đã gửi thông báo cho "${selectedUser!.full_name || selectedUser!.email}"`);
      }

      setShowCreateModal(false);
      resetCreateForm();
      fetchNotifications();
    } catch {
      toast.error('Không thể gửi thông báo');
    } finally {
      setCreating(false);
    }
  };

  const resetCreateForm = () => {
    setCreateForm({ title: '', body: '', notification_type: 'system', priority: 'normal', action_url: '' });
    setRecipientType('specific');
    setSelectedUser(null);
    setUserSearchInput('');
    setUserSearchResults([]);
  };

  // ── Pagination ────────────────────────────────────────────

  const totalPages = Math.max(1, Math.ceil(total / itemsPerPage));
  const startIdx = total > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
  const endIdx = Math.min(currentPage * itemsPerPage, total);

  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const maxVisible = 5;
    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (currentPage > 3) pages.push('...');
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);
      for (let i = start; i <= end; i++) pages.push(i);
      if (currentPage < totalPages - 2) pages.push('...');
      pages.push(totalPages);
    }
    return pages;
  };

  // ── Render ────────────────────────────────────────────────

  return (
    <div className={styles.page}>
      <Toaster richColors position="top-right" />

      {/* Header */}
      <div className={styles.pageHeader}>
        <div className={styles.pageTitle}>
          <h1>Quản lý thông báo</h1>
          <p>Quản lý và gửi thông báo đến người dùng trong hệ thống</p>
        </div>
        <button className={styles.btnPrimary} onClick={() => setShowCreateModal(true)}>
          <Plus size={18} />
          Gửi thông báo mới
        </button>
      </div>

      {/* Stats */}
      <div className={styles.statsGrid}>
        <StatCard icon={Bell} value={total} label="Tổng thông báo" color="default" />
        {/* <StatCard icon={Megaphone} value={0} label="Đã gửi hôm nay" color="default" /> */}
      </div>

      {/* Filters */}
      <div className={styles.filtersCard}>
        <div className={styles.filterGroup}>
          <label>Tìm kiếm</label>
          <div className={styles.searchBox}>
            <Search size={16} className={styles.searchIcon} />
            <input
              className={styles.searchInput}
              placeholder="Tìm theo tiêu đề, nội dung..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>
        </div>
        <div className={styles.filterGroup}>
          <label>Độ ưu tiên</label>
          <select
            className={styles.filterSelect}
            value={priorityFilter}
            onChange={(e) => { setPriorityFilter(e.target.value); setCurrentPage(1); }}
          >
            <option value="all">Tất cả</option>
            <option value="low">Thấp</option>
            <option value="normal">Bình thường</option>
            <option value="high">Cao</option>
          </select>
        </div>
        <div className={styles.filterGroup}>
          <label>Loại thông báo</label>
          <select
            className={styles.filterSelect}
            value={typeFilter}
            onChange={(e) => { setTypeFilter(e.target.value); setCurrentPage(1); }}
          >
            <option value="all">Tất cả loại</option>
            <option value="analysis_complete">Phân tích</option>
            <option value="system">Hệ thống</option>
            <option value="admin">Quản trị</option>
            <option value="info">Thông tin</option>
            <option value="warning">Cảnh báo</option>
          </select>
        </div>

      </div>

      {/* Table */}
      <div className={styles.tableCard}>
        <div className={styles.tableWrapper}>
          {loading ? (
            <div className={styles.loadingContainer}>
              <Loader2 size={24} className={styles.spin} />
              <p>Đang tải danh sách thông báo...</p>
            </div>
          ) : deduplicatedNotifs.length === 0 ? (
            <div className={styles.emptyState}>
              <BellOff size={48} />
              <p>Không tìm thấy thông báo nào</p>
              <span>Thử thay đổi bộ lọc hoặc gửi thông báo mới</span>
            </div>
          ) : (
            <table className={styles.dataTable}>
              <thead>
                <tr>
                  <th style={{ width: '40px' }}></th>
                  <th>Thông báo</th>
                  <th>Loại</th>
                  <th>Độ ưu tiên</th>
                  <th>Thời gian</th>
                  <th style={{ textAlign: 'right' }}>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {deduplicatedNotifs.map((notif) => {
                  const typeInfo = TYPE_DISPLAY[notif.notification_type] || { label: notif.notification_type, Icon: Bell, color: '#64748b', className: '' };
                  const prioInfo = PRIORITY_DISPLAY[notif.priority] || { label: notif.priority, className: '' };
                  const TypeIcon = typeInfo.Icon;
                  return (
                    <tr key={notif.notification_id}>
                      <td>
                        <span className={styles.notifIcon} style={{ color: typeInfo.color }}>
                          <TypeIcon size={18} />
                        </span>
                      </td>
                      <td>
                        <div
                          className={styles.notifCell}
                          onClick={() => handleViewDetail(notif)}
                          style={{ cursor: 'pointer' }}
                        >
                          <div className={styles.notifCellTitle}>
                            {notif.title}
                            {(notif as NotificationItem & { isBroadcast?: boolean }).isBroadcast && (
                              <span style={{
                                marginLeft: '8px', fontSize: '0.7rem', padding: '2px 6px', 
                                background: '#e0e7ff', color: '#4338ca', borderRadius: '4px', fontWeight: 600
                              }}>
                                Gửi tất cả
                              </span>
                            )}
                          </div>
                          <div className={styles.notifCellBody}>{notif.body}</div>
                        </div>
                      </td>

                      <td>
                        <span className={`${styles.badge} ${styles[typeInfo.className] || ''}`}>
                          {typeInfo.label}
                        </span>
                      </td>
                      <td>
                        <span className={`${styles.badge} ${styles[prioInfo.className] || ''}`}>
                          {prioInfo.label}
                        </span>
                      </td>
                      <td>
                        <span className={styles.timeText}>{getRelativeTime(notif.created_at)}</span>
                      </td>
                      <td>
                        <div className={styles.actionsCell}>
                          <button
                            className={`${styles.btnIcon} ${styles.btnView}`}
                            title="Xem chi tiết"
                            onClick={() => handleViewDetail(notif)}
                          >
                            <Eye size={14} />
                          </button>
                          <button
                            className={`${styles.btnIcon} ${styles.btnDelete}`}
                            title="Xóa"
                            onClick={() => confirmDelete(notif)}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {total > 0 && (
          <div className={styles.paginationBar}>
            <span className={styles.paginationInfo}>
              Hiển thị {startIdx} đến {endIdx} trong tổng số {total} thông báo
            </span>
            {totalPages > 1 && (
              <div className={styles.paginationControls}>
                <button
                  className={styles.paginationBtn}
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                >
                  <ChevronLeft size={14} /> Trước
                </button>
                {getPageNumbers().map((page, idx) =>
                  typeof page === 'string' ? (
                    <span key={`e-${idx}`} className={styles.pageDots}>…</span>
                  ) : (
                    <button
                      key={page}
                      className={`${styles.pageNumber} ${currentPage === page ? styles.pageNumberActive : ''}`}
                      onClick={() => setCurrentPage(page)}
                    >
                      {page}
                    </button>
                  )
                )}
                <button
                  className={styles.paginationBtn}
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                >
                  Tiếp <ChevronRight size={14} />
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ═══ Create Modal ═══ */}
      {showCreateModal && (
        <div className={styles.modalOverlay} onClick={() => !creating && setShowCreateModal(false)}>
          <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div>
                <h2>Gửi thông báo mới</h2>
                <p className={styles.modalSubtitle}>Gửi thông báo đến người dùng trong hệ thống</p>
              </div>
              <button className={styles.modalClose} onClick={() => !creating && setShowCreateModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCreate}>
              <div className={styles.modalBody}>
                {/* Recipient type toggle */}
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Đối tượng nhận</label>
                  <div style={{ display: 'flex', gap: '1rem', marginTop: '0.25rem' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer', fontWeight: recipientType === 'specific' ? 600 : 400 }}>
                      <input
                        type="radio"
                        name="recipientType"
                        value="specific"
                        checked={recipientType === 'specific'}
                        onChange={() => { setRecipientType('specific'); setSelectedUser(null); setUserSearchInput(''); setUserSearchResults([]); }}
                      />
                      Người dùng cụ thể
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer', fontWeight: recipientType === 'all' ? 600 : 400 }}>
                      <input
                        type="radio"
                        name="recipientType"
                        value="all"
                        checked={recipientType === 'all'}
                        onChange={() => { setRecipientType('all'); setSelectedUser(null); setUserSearchInput(''); setUserSearchResults([]); }}
                      />
                      <Users size={14} /> Tất cả người dùng
                    </label>
                  </div>
                </div>

                {/* Warning khi chọn broadcast */}
                {recipientType === 'all' && (
                  <div style={{
                    background: 'rgba(245,158,11,0.1)',
                    border: '1px solid rgba(245,158,11,0.4)',
                    borderRadius: '8px',
                    padding: '0.75rem 1rem',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.5rem',
                    color: '#b45309',
                    fontSize: '0.85rem',
                  }}>
                    <AlertCircle size={16} style={{ marginTop: '2px', flexShrink: 0 }} />
                    <span>
                      Thông báo sẽ được gửi đến <strong>tất cả người dùng đang hoạt động</strong> trong hệ thống.
                      Hãy kiểm tra kỹ nội dung trước khi gửi.
                    </span>
                  </div>
                )}

                {/* User selection (chỉ hiện khi specific) */}
                {recipientType === 'specific' && (
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>
                    Người nhận <span className={styles.required}>*</span>
                  </label>
                  {selectedUser ? (
                    <div className={styles.selectedUserChip}>
                      <div className={styles.selectedUserInfo}>
                        <span className={styles.selectedUserName}>{selectedUser.full_name || 'Không tên'}</span>
                        <span className={styles.selectedUserEmail}>{selectedUser.email}</span>
                      </div>
                      <button
                        type="button"
                        className={styles.chipRemove}
                        onClick={() => setSelectedUser(null)}
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ) : (
                    <div className={styles.userSearchWrap}>
                      <div className={styles.searchBox}>
                        <Search size={16} className={styles.searchIcon} />
                        <input
                          className={styles.searchInput}
                          placeholder="Tìm người dùng theo tên hoặc email..."
                          value={userSearchInput}
                          onChange={(e) => setUserSearchInput(e.target.value)}
                        />
                      </div>
                      {(userSearchResults.length > 0 || loadingUsers) && (
                        <div className={styles.userDropdown}>
                          {loadingUsers ? (
                            <div className={styles.userDropdownLoading}>
                              <Loader2 size={14} className={styles.spin} /> Đang tìm...
                            </div>
                          ) : (
                            userSearchResults.map(u => (
                              <button
                                key={u.id}
                                type="button"
                                className={styles.userDropdownItem}
                                onClick={() => {
                                  setSelectedUser(u);
                                  setUserSearchInput('');
                                  setUserSearchResults([]);
                                }}
                              >
                                <div className={styles.userDropdownName}>{u.full_name || 'Không tên'}</div>
                                <div className={styles.userDropdownEmail}>{u.email}</div>
                              </button>
                            ))
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
                )}

                {/* Title */}
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>
                    Tiêu đề <span className={styles.required}>*</span>
                  </label>
                  <input
                    className={styles.formInput}
                    placeholder="Nhập tiêu đề thông báo..."
                    value={createForm.title}
                    onChange={(e) => setCreateForm(f => ({ ...f, title: e.target.value }))}
                    maxLength={255}
                  />
                </div>

                {/* Body */}
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>
                    Nội dung <span className={styles.required}>*</span>
                  </label>
                  <textarea
                    className={styles.formTextarea}
                    placeholder="Nhập nội dung thông báo..."
                    value={createForm.body}
                    onChange={(e) => setCreateForm(f => ({ ...f, body: e.target.value }))}
                    rows={4}
                  />
                </div>

                {/* Type + Priority */}
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Loại thông báo</label>
                    <select
                      className={styles.formSelect}
                      value={createForm.notification_type}
                      onChange={(e) => setCreateForm(f => ({ ...f, notification_type: e.target.value }))}
                    >
                      {NOTIF_TYPE_OPTIONS.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Độ ưu tiên</label>
                    <select
                      className={styles.formSelect}
                      value={createForm.priority}
                      onChange={(e) => setCreateForm(f => ({ ...f, priority: e.target.value }))}
                    >
                      {PRIORITY_OPTIONS.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Action URL */}
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>URL hành động (tùy chọn)</label>
                  <input
                    className={styles.formInput}
                    placeholder="/analysis-result/123 hoặc https://..."
                    value={createForm.action_url}
                    onChange={(e) => setCreateForm(f => ({ ...f, action_url: e.target.value }))}
                  />
                  <span className={styles.formHint}>Đường dẫn người dùng sẽ điều hướng khi nhấn vào thông báo</span>
                </div>
              </div>
              <div className={styles.modalFooter}>
                <button
                  type="button"
                  className={styles.btnCancel}
                  onClick={() => { setShowCreateModal(false); resetCreateForm(); }}
                  disabled={creating}
                >
                  Hủy
                </button>
                <button type="submit" className={styles.btnSubmit} disabled={creating}>
                  {creating ? (
                    <><Loader2 size={16} className={styles.spin} /> Đang gửi...</>
                  ) : (
                    <><Send size={16} /> Gửi thông báo</>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ═══ Detail Modal ═══ */}
      {showDetail && selectedNotif && (
        <div className={styles.modalOverlay} onClick={() => setShowDetail(false)}>
          <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div>
                <h2>Chi tiết thông báo</h2>
                <p className={styles.modalSubtitle}>Thông tin chi tiết về thông báo này</p>
              </div>
              <button className={styles.modalClose} onClick={() => setShowDetail(false)}>
                <X size={20} />
              </button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.detailGrid}>
                <div className={styles.detailItem}>
                  <p className={styles.detailLabel}>Tiêu đề</p>
                  <p className={styles.detailValue}>{selectedNotif.title}</p>
                </div>
                <div className={styles.detailItem}>
                  <p className={styles.detailLabel}>Loại</p>
                  <span className={`${styles.badge} ${styles[(TYPE_DISPLAY[selectedNotif.notification_type]?.className) || '']}`}>
                    {TYPE_DISPLAY[selectedNotif.notification_type]?.icon || '🔔'} {TYPE_DISPLAY[selectedNotif.notification_type]?.label || selectedNotif.notification_type}
                  </span>
                </div>
                <div className={styles.detailItem}>
                  <p className={styles.detailLabel}>Độ ưu tiên</p>
                  <span className={`${styles.badge} ${styles[(PRIORITY_DISPLAY[selectedNotif.priority]?.className) || '']}`}>
                    {PRIORITY_DISPLAY[selectedNotif.priority]?.label || selectedNotif.priority}
                  </span>
                </div>
                <div className={styles.detailItem}>
                  <p className={styles.detailLabel}>Trạng thái</p>
                  <span className={`${styles.badge} ${selectedNotif.is_read ? styles.statusRead : styles.statusUnread}`}>
                    {selectedNotif.is_read ? '✓ Đã đọc' : '● Chưa đọc'}
                  </span>
                </div>
                <div className={styles.detailItem}>
                  <p className={styles.detailLabel}>Ngày tạo</p>
                  <p className={styles.detailValue}>{formatDateTime(selectedNotif.created_at)}</p>
                </div>
                <div className={styles.detailItem}>
                  <p className={styles.detailLabel}>Ngày đọc</p>
                  <p className={styles.detailValue}>{selectedNotif.read_at ? formatDateTime(selectedNotif.read_at) : '—'}</p>
                </div>
              </div>
              <div className={styles.detailBodyBox}>
                <p className={styles.detailLabel}>Nội dung</p>
                <div className={styles.detailBodyContent}>{selectedNotif.body}</div>
              </div>
              {selectedNotif.action_url && (
                <div className={styles.detailItem} style={{ marginTop: '0.75rem' }}>
                  <p className={styles.detailLabel}>URL hành động</p>
                  <p className={`${styles.detailValue} ${styles.mono}`}>{selectedNotif.action_url}</p>
                </div>
              )}
              {selectedNotif.data && Object.keys(selectedNotif.data).length > 0 && (
                <div className={styles.detailDataBox}>
                  <p className={styles.detailLabel}>Dữ liệu đính kèm</p>
                  <pre>{JSON.stringify(selectedNotif.data, null, 2)}</pre>
                </div>
              )}
            </div>
            <div className={styles.modalFooter}>
              <button className={styles.btnCancel} onClick={() => setShowDetail(false)}>
                Đóng
              </button>
              {!selectedNotif.is_read && (
                <button
                  className={styles.btnSubmit}
                  onClick={() => { handleMarkRead(selectedNotif); setShowDetail(false); }}
                >
                  <Check size={16} /> Đánh dấu đã đọc
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ═══ Delete Confirm ═══ */}
      {showDeleteConfirm && deleteTarget && (
        <div className={styles.modalOverlay} onClick={() => !deleting && setShowDeleteConfirm(false)}>
          <div className={`${styles.modalContent} ${styles.confirmContent}`} onClick={e => e.stopPropagation()}>
            <div className={styles.modalBody}>
              <div className={styles.confirmIcon}>
                <AlertCircle size={24} />
              </div>
              <h3 className={styles.confirmTitle}>Xóa thông báo</h3>
              <p className={styles.confirmMessage}>
                Bạn có chắc chắn muốn xóa thông báo <strong>"{deleteTarget.title}"</strong>?
                Hành động này không thể hoàn tác.
              </p>
            </div>
            <div className={styles.modalFooter}>
              <button className={styles.btnCancel} onClick={() => setShowDeleteConfirm(false)} disabled={deleting}>
                Hủy
              </button>
              <button className={styles.btnDanger} onClick={handleDelete} disabled={deleting}>
                {deleting ? (
                  <><Loader2 size={16} className={styles.spin} /> Đang xóa...</>
                ) : (
                  <><Trash2 size={16} /> Xóa</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
