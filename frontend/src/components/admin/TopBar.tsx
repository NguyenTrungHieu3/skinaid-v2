import { useState, useEffect, useRef, useCallback } from "react";
import { Bell, ChevronRight, AlertTriangle, LogOut, Home, XCircle, CheckCircle, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../contexts/AuthContext";
import * as notificationService from "../../services/notificationService";
import type { NotificationItem } from "../../services/notificationService";
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



const getLevelStyle = (severity: string) => {
  if (severity === 'error') {
    return { icon: XCircle, color: '#ef4444', badge: '#fee2e2' };
  }
  if (severity === 'warning') {
    return { icon: AlertTriangle, color: '#f59e0b', badge: '#fef3c7' };
  }
  return { icon: Bell, color: '#17805f', badge: '#dcfce7' };
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

  // Alert state — shows notifications
  const [showNotifs, setShowNotifs] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifLoading, setNotifLoading] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const count = await notificationService.getUnreadCount();
      setUnreadCount(count);
    } catch {
      // silent fail
    }
  }, []);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 60000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  const openNotifs = async () => {
    setShowNotifs(true);
    setNotifLoading(true);
    try {
      const res = await notificationService.getNotifications({ limit: 5 });
      setNotifications(res.items);
      setUnreadCount(res.unread_count);
    } catch {
      // silent
    } finally {
      setNotifLoading(false);
    }
  };

  const toggleNotifs = () => {
    if (showNotifs) {
      setShowNotifs(false);
    } else {
      openNotifs();
    }
  };

  const handleMarkAsRead = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await notificationService.markAsRead(id);
      setNotifications(prev => prev.map(n => n.notification_id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch {}
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {}
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
      if (showNotifs && notifRef.current && !notifRef.current.contains(event.target as Node)) {
        setShowNotifs(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showLogoutMenu, showNotifs]);

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
            <div className={styles.notifContainer} ref={notifRef}>
              <button
                className={`${styles.bellBtn} ${showNotifs ? styles.bellBtnActive : ''}`}
                title="Thông báo"
                onClick={toggleNotifs}
              >
                <Bell size={20} />
                {unreadCount > 0 && (
                  <span className={styles.bellBadge}>
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </button>

              {/* Alert Dropdown */}
              {showNotifs && (
                <div className={styles.notifPanel}>
                  <div className={styles.notifHeader}>
                    <div className={styles.notifHeaderTitle}>
                      <Bell size={15} className={styles.headerAlertIcon} />
                      <h3>Thông báo</h3>
                    </div>
                    <div className={styles.notifHeaderActions}>
                      {unreadCount > 0 && (
                        <button className={styles.notifMarkAllBtn} onClick={handleMarkAllRead}>
                          Đánh dấu đã đọc
                        </button>
                      )}
                      <button
                        className={styles.notifViewAllBtn}
                        onClick={() => { setShowNotifs(false); onPageChange?.('notifications'); }}
                      >
                        Xem tất cả
                      </button>
                    </div>
                  </div>

                  <div className={styles.notifList}>
                    {notifLoading ? (
                      <div className={styles.notifLoading}>
                        <Loader2 size={20} className={styles.spin} />
                        <span>Đang tải...</span>
                      </div>
                    ) : notifications.length === 0 ? (
                      <div className={styles.notifEmpty}>
                        <CheckCircle size={32} color="#10b981" />
                        <p>Không có thông báo nào</p>
                        <span>Bạn đã xem hết thông báo</span>
                      </div>
                    ) : (
                      notifications.map((notif) => {
                        const lv = getLevelStyle(notif.severity || 'info');
                        const Icon = lv.icon;
                        return (
                          <div
                            key={notif.notification_id}
                            className={`${styles.notifItem} ${!notif.is_read ? styles.notifItemUnread : ''}`}
                            style={{ borderLeftColor: lv.color, cursor: 'pointer' }}
                            onClick={() => {
                              setShowNotifs(false);
                              onPageChange?.(`notification_detail_${notif.notification_id}`);
                            }}
                          >
                            <div className={styles.notifIconWrap} style={{ background: lv.badge }}>
                              <Icon size={16} color={lv.color} />
                            </div>
                            <div className={styles.notifContent}>
                              <div className={styles.notifTitle}>{notif.title}</div>
                              <div className={styles.notifBody}>{notif.body}</div>
                              <div className={styles.notifMeta}>
                                <span className={styles.notifTime}>
                                  {getRelativeTime(notif.created_at)}
                                </span>
                              </div>
                            </div>
                            {!notif.is_read && (
                              <div className={styles.notifActions}>
                                <button
                                  className={styles.notifDeleteBtn}
                                  onClick={(e) => handleMarkAsRead(notif.notification_id, e)}
                                  title="Đánh dấu đã đọc"
                                >
                                  <CheckCircle size={13} />
                                </button>
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
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
