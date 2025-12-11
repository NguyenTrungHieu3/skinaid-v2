import { useState, useEffect } from "react";
import { AlertTriangle, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import CountryFlag from "react-country-flag";
import { useAuth } from "../../contexts/AuthContext";
import styles from "./TopBar.module.css";

export default function TopBar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { i18n, t } = useTranslation();
  const [showLogoutMenu, setShowLogoutMenu] = useState(false);

  // State mới để điều khiển Modal xác nhận
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

  // 1. Khi bấm nút Logout ở menu thả xuống -> Mở Modal, đóng menu
  const onLogoutClick = () => {
    setShowLogoutMenu(false);
    setShowLogoutConfirm(true);
  };

  // 2. Khi bấm xác nhận trong Modal -> Thực hiện Logout thật
  const handleConfirmLogout = () => {
    logout();
    setShowLogoutConfirm(false);
    navigate("/");
  };

  // 3. Khi bấm hủy -> Đóng Modal
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

  const LanguageSwitcher = () => (
    <div className={styles.languageSwitcher}>
      <button
        onClick={() => i18n.changeLanguage("en")}
        className={`${styles.flagButton} ${
          i18n.language === "en" ? styles.activeFlag : ""
        }`}
        aria-label="Switch to English"
        title="English"
      >
        <CountryFlag countryCode="US" svg />
      </button>
      <span className={styles.divider}>|</span>
      <button
        onClick={() => i18n.changeLanguage("vi")}
        className={`${styles.flagButton} ${
          i18n.language === "vi" ? styles.activeFlag : ""
        }`}
        aria-label="Switch to Vietnamese"
        title="Tiếng Việt"
      >
        <CountryFlag countryCode="VN" svg />
      </button>
    </div>
  );

  return (
    <>
      <header className={styles.adminTopbar}>
        <div className={styles.adminTopbarContent}>
          <div className={styles.adminTopbarActions}>
            <LanguageSwitcher />
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
                  {/* Thay đổi hàm gọi ở đây thành onLogoutClick */}
                  <button
                    className={styles.logoutMenuButton}
                    onClick={(e) => {
                      e.stopPropagation(); // Ngăn sự kiện nổi bọt
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
