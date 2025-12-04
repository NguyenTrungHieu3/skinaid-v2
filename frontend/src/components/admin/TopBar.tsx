import { useState, useEffect } from 'react';
import { LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import CountryFlag from "react-country-flag";
import { useAuth } from '../../contexts/AuthContext';
import styles from './TopBar.module.css';

export default function TopBar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { i18n, t } = useTranslation();
  const [showLogoutMenu, setShowLogoutMenu] = useState(false);

  // Close logout menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showLogoutMenu && !(event.target as Element).closest(`.${styles.adminUserInfo}`)) {
        setShowLogoutMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showLogoutMenu]);

  // Handle logout
  const handleLogout = () => {
    if (window.confirm(t('admin.topbar.logout_confirm'))) {
      logout();
      navigate('/login');
    }
  };

  // Get initials from display name for avatar
  const getInitials = (name: string | undefined | null) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const displayName = user?.full_name || user?.user_name || 'Admin User';

  let role = t('admin.topbar.roles.user');
  if (user?.roles && user.roles.length > 0) {
    const userRole = user.roles[0].toLowerCase();
    const roleMap: Record<string, string> = {
      'admin': t('admin.topbar.roles.admin'),
      'moderator': t('admin.topbar.roles.moderator'),
      'user': t('admin.topbar.roles.user')
    };
    role = roleMap[userRole] || userRole.charAt(0).toUpperCase() + userRole.slice(1);
  }

  const LanguageSwitcher = () => (
    <div className={styles.languageSwitcher}>
      <button
        onClick={() => i18n.changeLanguage("en")}
        className={`${styles.flagButton} ${i18n.language === "en" ? styles.activeFlag : ""}`}
        aria-label="Switch to English"
        title="English"
      >
        <CountryFlag countryCode="US" svg />
      </button>
      <span className={styles.divider}>|</span>
      <button
        onClick={() => i18n.changeLanguage("vi")}
        className={`${styles.flagButton} ${i18n.language === "vi" ? styles.activeFlag : ""}`}
        aria-label="Switch to Vietnamese"
        title="Tiếng Việt"
      >
        <CountryFlag countryCode="VN" svg />
      </button>
    </div>
  );

  return (
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
                <button className={styles.logoutMenuButton} onClick={handleLogout}>
                  <LogOut size={16} />
                  <span>{t('admin.topbar.logout')}</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
