import { useState, useEffect } from "react";
import { Menu, Bell, ChevronRight, AlertTriangle, LogOut, Home } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../contexts/AuthContext";
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
};

interface TopBarProps {
  onToggleSidebar?: () => void;
  currentPage?: string;
  onPageChange?: (page: string) => void;
}

export default function TopBar({ onToggleSidebar, currentPage, onPageChange }: TopBarProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { i18n, t } = useTranslation();
  const [showLogoutMenu, setShowLogoutMenu] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  // Close logout menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        showLogoutMenu &&
        !(event.target as Element).closest(`.${styles.adminUserInfo}`)
      ) {
        setShowLogoutMenu(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showLogoutMenu]);

  const onLogoutClick = () => {
    setShowLogoutMenu(false);
    setShowLogoutConfirm(true);
  };

  const handleConfirmLogout = () => {
    logout();
    setShowLogoutConfirm(false);
    navigate("/");
  };

  const handleCancelLogout = () => {
    setShowLogoutConfirm(false);
  };

  // Get initials from display name for avatar
  const getInitials = (name: string | undefined | null) => {
    if (!name) return "U";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
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
    role =
      roleMap[userRole] || userRole.charAt(0).toUpperCase() + userRole.slice(1);
  }

  const currentLabel = PAGE_LABELS[currentPage || 'dashboard'] || 'Tổng quan';

  return (
    <>
      <header className={styles.adminTopbar}>
        <div className={styles.adminTopbarContent}>
          {/* Left side: hamburger + breadcrumb */}
          <div className={styles.adminTopbarLeft}>
            {/* Breadcrumb */}
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

          {/* Right side: bell + user */}
          <div className={styles.adminTopbarActions}>
            {/* Notification bell */}
            <button className={styles.bellBtn} title="Thông báo">
              <Bell size={20} />
              <span className={styles.bellBadge}>3</span>
            </button>

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

              {/* Logout Menu */}
              {showLogoutMenu && (
                <div className={styles.logoutMenu}>
                  <div className={styles.logoutMenuHeader}>
                    <p className={styles.logoutMenuName}>{displayName}</p>
                    <p className={styles.logoutMenuEmail}>{user?.email}</p>
                  </div>
                  <div className={styles.logoutMenuDivider}></div>
                  <button
                    className={styles.logoutMenuButton}
                    onClick={(e) => {
                      e.stopPropagation();
                      onLogoutClick();
                    }}
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

      {/* --- Logout Confirmation Modal --- */}
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
              {t("admin.top_bar.logout_confirm") ||
                "Bạn có chắc chắn muốn đăng xuất khỏi hệ thống không?"}
            </p>
            <div className={styles.modalActions}>
              <button className={styles.cancelBtn} onClick={handleCancelLogout}>
                {t("admin.top_bar.cancel") || "Hủy bỏ"}
              </button>
              <button
                className={styles.confirmBtn}
                onClick={handleConfirmLogout}
              >
                {t("admin.top_bar.logout") || "Đăng xuất"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
