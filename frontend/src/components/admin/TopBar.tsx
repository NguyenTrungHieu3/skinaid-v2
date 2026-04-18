import { useState, useEffect, useRef, useCallback } from "react";
import { Bell, ChevronRight, AlertTriangle, LogOut, Home, AlertCircle, XCircle, CheckCircle, Loader2, BellOff } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../contexts/AuthContext";
import { getAuditLogs } from "../../services/auditService";
import type { AuditLog } from "../../services/auditService";
import styles from "./TopBar.module.css";

// Map page ids to Vietnamese labels for breadcrumb
const PAGE_LABELS: Record<string, string> = {
  dashboard: 'Tổng quan',
  users: 'Quản lý người dùng',
  firstaid: 'Hướng dẫn sơ cứu',
  questionnaires: 'Bộ câu hỏi',
  models: 'Quản lý Model',
  rag: 'Knowledge Base',
  logs: 'Nhật ký hệ thống',
  notifications: 'Thông báo',
};

// Label map for audit actions
const ACTION_LABELS: Record<string, string> = {
  ai_analysis_failed: 'Phân tích AI thất bại',
  rag_indexing_failed: 'Đánh chỉ mục RAG thất bại',
  llm_error: 'Lỗi LLM',
  auth_failed: 'Xác thực thất bại',
  upload_failed: 'Tải lên thất bại',
  system_error: 'Lỗi hệ thống',
};

const getLevelStyle = (level: string, success: boolean) => {
  if (!success || level === 'error') {
    return { icon: XCircle, color: '#ef4444', badge: '#fee2e2' };
  }
  if (level === 'warning') {
    return { icon: AlertTriangle, color: '#f59e0b', badge: '#fef3c7' };
  }
  return { icon: CheckCircle, color: '#17805f', badge: '#dcfce7' };
};

interface TopBarProps {
  onToggleSidebar?: () => void;
  currentPage?: string;
  onPageChange?: (page: string) => void;
}

export default function TopBar({ onToggleSidebar, currentPage, onPageChange }: TopBarProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { t } = useTranslation();
  const [showLogoutMenu, setShowLogoutMenu] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  // Alert state — shows audit error/warning logs
  const [showAlerts, setShowAlerts] = useState(false);
  const [alerts, setAlerts] = useState<AuditLog[]>([]);
  const [alertCount, setAlertCount] = useState(0);
  const [alertLoading, setAlertLoading] = useState(false);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  const alertRef = useRef<HTMLDivElement>(null);

  // Fetch count of failed events
  const fetchAlertCount = useCallback(async () => {
    try {
      const res = await getAuditLogs({ success: false, limit: 50, page: 1 });
      if (res.success && res.data) {
        const undismissed = res.data.logs.filter(
          (l: AuditLog) => !dismissed.has(l.audit_action_id)
        );
        setAlertCount(undismissed.length);
      }
    } catch {
      // silent fail
    }
  }, [dismissed]);

  useEffect(() => {
    fetchAlertCount();
    const interval = setInterval(fetchAlertCount, 60000);
    return () => clearInterval(interval);
  }, [fetchAlertCount]);

  // Open alert panel
  const openAlerts = async () => {
    setShowAlerts(true);
    setAlertLoading(true);
    try {
      const res = await getAuditLogs({ success: false, limit: 20, page: 1 });
      if (res.success && res.data) {
        setAlerts(res.data.logs);
        const undismissed = res.data.logs.filter(
          (l: AuditLog) => !dismissed.has(l.audit_action_id)
        );
        setAlertCount(undismissed.length);
      }
    } catch {
      // silent
    } finally {
      setAlertLoading(false);
    }
  };

  const toggleAlerts = () => {
    if (showAlerts) {
      setShowAlerts(false);
    } else {
      openAlerts();
    }
  };

  const dismissAlert = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDismissed(prev => new Set([...prev, id]));
    setAlerts(prev => prev.filter(a => a.audit_action_id !== id));
    setAlertCount(prev => Math.max(0, prev - 1));
  };

  const dismissAll = () => {
    const ids = alerts.map(a => a.audit_action_id);
    setDismissed(prev => new Set([...prev, ...ids]));
    setAlerts([]);
    setAlertCount(0);
  };

  const getRelativeTime = (dateStr: string) => {
    const d = dateStr.endsWith("Z") ? dateStr : `${dateStr}Z`;
    const ms = Date.now() - new Date(d).getTime();
    const sec = Math.floor(ms / 1000);
    if (sec < 60) return "Vừa xong";
    const min = Math.floor(sec / 60);
    if (min < 60) return `${min} phút trước`;
    const hr = Math.floor(min / 60);
    if (hr < 24) return `${hr} giờ trước`;
    const day = Math.floor(hr / 24);
    return `${day} ngày trước`;
  };

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showLogoutMenu && !(event.target as Element).closest(`.${styles.adminUserInfo}`)) {
        setShowLogoutMenu(false);
      }
      if (showAlerts && alertRef.current && !alertRef.current.contains(event.target as Node)) {
        setShowAlerts(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showLogoutMenu, showAlerts]);

  const onLogoutClick = () => {
    setShowLogoutMenu(false);
    setShowLogoutConfirm(true);
  };

  const handleConfirmLogout = () => {
    logout();
    setShowLogoutConfirm(false);
    navigate("/");
  };

  const handleCancelLogout = () => setShowLogoutConfirm(false);

  const getInitials = (name: string | undefined | null) => {
    if (!name) return "U";
    return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
  };

  const displayName = user?.full_name || user?.user_name || "Admin User";

  let role = t("admin.top_bar.roles.user");
  if (user?.roles && user.roles.length > 0) {
    const userRole = user.roles[0].toLowerCase();
    const roleMap: Record<string, string> = {
      admin: t("admin.top_bar.roles.admin"),
      moderator: t("admin.top_bar.roles.moderator"),
      user: t("admin.top_bar.roles.user"),
    };
    role = roleMap[userRole] || userRole.charAt(0).toUpperCase() + userRole.slice(1);
  }

  const currentLabel = PAGE_LABELS[currentPage || 'dashboard'] || 'Tổng quan';

  return (
    <>
      <header className={styles.adminTopbar}>
        <div className={styles.adminTopbarContent}>
          {/* Left: breadcrumb */}
          <div className={styles.adminTopbarLeft}>
            <nav className={styles.breadcrumb} aria-label="Breadcrumb">
              <button
                className={styles.breadcrumbLink}
                onClick={() => onPageChange?.('dashboard')}
                title="Về trang tổng quan"
              >
                <Home size={14} />
                <span>Admin</span>
              </button>
              {currentPage && currentPage !== 'dashboard' && (
                <>
                  <ChevronRight size={14} className={styles.breadcrumbSep} />
                  <span className={styles.breadcrumbCurrent}>{currentLabel}</span>
                </>
              )}
            </nav>
          </div>

          {/* Right: bell + user */}
          <div className={styles.adminTopbarActions}>
            {/* Alert Bell */}
            <div className={styles.notifContainer} ref={alertRef}>
              <button
                className={`${styles.bellBtn} ${showAlerts ? styles.bellBtnActive : ''}`}
                title="Cảnh báo hệ thống"
                onClick={toggleAlerts}
              >
                <Bell size={20} />
                {alertCount > 0 && (
                  <span className={styles.bellBadge}>
                    {alertCount > 99 ? '99+' : alertCount}
                  </span>
                )}
              </button>

              {/* Alert Dropdown */}
              {showAlerts && (
                <div className={styles.notifPanel}>
                  <div className={styles.notifHeader}>
                    <div className={styles.notifHeaderTitle}>
                      <AlertCircle size={15} className={styles.headerAlertIcon} />
                      <h3>Cảnh báo hệ thống</h3>
                    </div>
                    <div className={styles.notifHeaderActions}>
                      {alerts.length > 0 && (
                        <button className={styles.notifMarkAllBtn} onClick={dismissAll}>
                          Bỏ qua tất cả
                        </button>
                      )}
                      <button
                        className={styles.notifViewAllBtn}
                        onClick={() => { setShowAlerts(false); onPageChange?.('logs'); }}
                      >
                        Xem nhật ký
                      </button>
                    </div>
                  </div>

                  <div className={styles.notifList}>
                    {alertLoading ? (
                      <div className={styles.notifLoading}>
                        <Loader2 size={20} className={styles.spin} />
                        <span>Đang tải...</span>
                      </div>
                    ) : alerts.length === 0 ? (
                      <div className={styles.notifEmpty}>
                        <BellOff size={32} />
                        <p>Không có cảnh báo nào</p>
                        <span>Hệ thống đang hoạt động bình thường</span>
                      </div>
                    ) : (
                      alerts.map((alert) => {
                        const lv = getLevelStyle(alert.level, alert.success);
                        const Icon = lv.icon;
                        const label = ACTION_LABELS[alert.action] || alert.action;
                        return (
                          <div
                            key={alert.audit_action_id}
                            className={`${styles.notifItem} ${styles.notifItemUnread}`}
                            style={{ borderLeftColor: lv.color }}
                          >
                            <div className={styles.notifIconWrap} style={{ background: lv.badge }}>
                              <Icon size={16} color={lv.color} />
                            </div>
                            <div className={styles.notifContent}>
                              <div className={styles.notifTitle}>{label}</div>
                              {alert.description && (
                                <div className={styles.notifBody}>{alert.description}</div>
                              )}
                              {alert.error_message && (
                                <div className={`${styles.notifBody} ${styles.notifError}`}>
                                  {alert.error_message}
                                </div>
                              )}
                              <div className={styles.notifMeta}>
                                <span
                                  className={styles.notifType}
                                  style={{ color: lv.color, background: lv.badge }}
                                >
                                  {!alert.success || alert.level === 'error' ? 'Lỗi' : 'Cảnh báo'}
                                </span>
                                {alert.resource_type && (
                                  <span className={styles.notifResource}>{alert.resource_type}</span>
                                )}
                                <span className={styles.notifTime}>
                                  {getRelativeTime(alert.timestamp)}
                                </span>
                              </div>
                            </div>
                            <div className={styles.notifActions}>
                              <button
                                className={styles.notifDeleteBtn}
                                onClick={(e) => dismissAlert(alert.audit_action_id, e)}
                                title="Bỏ qua"
                              >
                                <XCircle size={13} />
                              </button>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>

                  {alerts.length > 0 && (
                    <div className={styles.notifFooter}>
                      <span>{alerts.length} sự kiện lỗi gần đây</span>
                      <button
                        className={styles.notifFooterLink}
                        onClick={() => { setShowAlerts(false); onPageChange?.('logs'); }}
                      >
                        Xem chi tiết →
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className={styles.topbarDivider} />

            <div
              className={styles.adminUserInfo}
              title={user?.email}
              onClick={() => setShowLogoutMenu(!showLogoutMenu)}
            >
              <div className={styles.adminUserText}>
                <p>{displayName}</p>
                <p>{role}</p>
              </div>
              <div className={styles.adminUserAvatar}>
                {getInitials(displayName)}
              </div>

              {showLogoutMenu && (
                <div className={styles.logoutMenu}>
                  <div className={styles.logoutMenuHeader}>
                    <p className={styles.logoutMenuName}>{displayName}</p>
                    <p className={styles.logoutMenuEmail}>{user?.email}</p>
                  </div>
                  <div className={styles.logoutMenuDivider}></div>
                  <button
                    className={styles.logoutMenuButton}
                    onClick={(e) => { e.stopPropagation(); onLogoutClick(); }}
                  >
                    <LogOut size={16} />
                    <span>{t("admin.top_bar.logout")}</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Logout Confirmation Modal */}
      {showLogoutConfirm && (
        <div className={styles.modalOverlay}>
          <div className={styles.modalContent}>
            <div className={styles.modalIcon}>
              <AlertTriangle size={24} />
            </div>
            <h3 className={styles.modalTitle}>
              {t("admin.top_bar.logout_confirm_title") || "Xác nhận đăng xuất"}
            </h3>
            <p className={styles.modalMessage}>
              {t("admin.top_bar.logout_confirm") || "Bạn có chắc chắn muốn đăng xuất khỏi hệ thống không?"}
            </p>
            <div className={styles.modalActions}>
              <button className={styles.cancelBtn} onClick={handleCancelLogout}>
                {t("admin.top_bar.cancel") || "Hủy bỏ"}
              </button>
              <button className={styles.confirmBtn} onClick={handleConfirmLogout}>
                {t("admin.top_bar.logout") || "Đăng xuất"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
