import { useState, useEffect } from 'react';
import { LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import styles from './TopBar.module.css';

export default function TopBar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
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
    if (window.confirm('Are you sure you want to logout?')) {
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

  let role = 'User';
  if (user?.roles && user.roles.length > 0) {
    const userRole = user.roles[0].toLowerCase();
    const roleMap: Record<string, string> = {
      'admin': 'Administrator',
      'moderator': 'Moderator',
      'user': 'User'
    };
    role = roleMap[userRole] || userRole.charAt(0).toUpperCase() + userRole.slice(1);
  }

  return (
    <header className={styles.adminTopbar}>
      <div className={styles.adminTopbarContent}>
        <div className={styles.adminTopbarActions}>
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
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
