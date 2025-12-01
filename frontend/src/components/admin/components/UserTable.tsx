import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { MoreVertical, Edit2, RotateCw, Trash2 } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import styles from './UserTable.module.css';

interface User {
  user_id: string;
  email: string;
  user_name: string;
  display_name: string;
  roles: string[];
  is_active: boolean;
  upload_count?: number;
  created_at: string;
}

interface UserTableProps {
  users: User[];
  loading: boolean;
  onEdit: (user: User) => void;
  onDelete: (userId: string, userName: string) => void;
  onToggleStatus: (userId: string, currentStatus: boolean) => void;
  actionMenuOpen: string | null;
  setActionMenuOpen: (id: string | null) => void;
  isSubmitting: boolean;
  isDeletingUser: string | null;
  isTogglingStatus: string | null;
}

const UserTable: React.FC<UserTableProps> = ({
  users,
  loading,
  onEdit,
  onDelete,
  onToggleStatus,
  actionMenuOpen,
  setActionMenuOpen,
  isSubmitting,
  isDeletingUser,
  isTogglingStatus
}) => {
  const { t } = useTranslation();
  const { user: currentUser } = useAuth();
  const [menuPosition, setMenuPosition] = useState<{ top: number; right: number } | null>(null);

  // Function to translate role
  const translateRole = (role: string) => {
    const roleLower = role.toLowerCase();
    return t(`admin.user_management.roles.${roleLower}`) || role;
  };

  // Close action menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (
        actionMenuOpen &&
        !target.closest(`.${styles.actionsMenu}`) &&
        !target.closest('.user-actions-dropdown-portal')
      ) {
        setActionMenuOpen(null);
      }
    };

    if (actionMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [actionMenuOpen, setActionMenuOpen]);

  // Get initials for avatar
  const getInitials = (name: string) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toISOString().split('T')[0];
  };

  // Get role badge class
  const getRoleBadgeClass = (roles: string[]) => {
    const role = (roles[0] || 'user').toLowerCase();
    if (role === 'admin') {
      return styles.adminBadgePurple;
    }
    return styles.adminBadgeBlue;
  };

  if (loading) {
    return (
      <div className={styles.adminCard}>
        <div className={styles.adminCardContent} style={{ padding: '3rem', textAlign: 'center' }}>
          <p>{t('admin.user_management.table.loading')}</p>
        </div>
      </div>
    );
  }

  if (!loading && users.length === 0) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>👥</div>
        <p>{t('admin.user_management.table.no_users')}</p>
        <p className={styles.emptySubtitle}>{t('admin.user_management.table.adjust_filters')}</p>
      </div>
    );
  }

  return (
    <div className={styles.adminCard}>
      <div className={styles.adminCardContent}>
        <table className={styles.userTable}>
          <thead>
            <tr>
              <th>{t('admin.user_management.table.headers.name')}</th>
              <th>{t('admin.user_management.table.headers.email')}</th>
              <th>{t('admin.user_management.table.headers.role')}</th>
              <th>{t('admin.user_management.table.headers.status')}</th>
              <th>{t('admin.user_management.table.headers.uploads')}</th>
              <th>{t('admin.user_management.table.headers.join_date')}</th>
              <th>{t('admin.user_management.table.headers.actions')}</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.user_id}>
                <td>
                  <div className={styles.userInfo}>
                    <div className={styles.userAvatar}>
                      {getInitials(user.display_name || user.email)}
                    </div>
                    <span>{user.display_name || t('admin.user_management.table.no_name')}</span>
                  </div>
                </td>
                <td>{user.email}</td>
                <td>
                  <span className={`${styles.adminBadge} ${getRoleBadgeClass(user.roles)}`}>
                    {translateRole(user.roles[0] || 'user')}
                  </span>
                </td>
                <td>
                  <span className={`${styles.adminBadge} ${user.is_active ? styles.adminBadgeSuccess : styles.adminBadgeGray}`}>
                    {user.is_active ? t('admin.user_management.table.status_active') : t('admin.user_management.table.status_inactive')}
                  </span>
                </td>
                <td>{user.upload_count || 0}</td>
                <td>{formatDate(user.created_at)}</td>
                <td>
                  <div className={styles.actionsMenu}>
                    {currentUser?.user_id !== user.user_id && (
                      <>
                        <button
                          className={styles.actionsTrigger}
                          onClick={(e) => {
                            const rect = e.currentTarget.getBoundingClientRect();
                            setMenuPosition({
                              top: rect.top,
                              right: window.innerWidth - rect.left + 8
                            });
                            setActionMenuOpen(actionMenuOpen === user.user_id ? null : user.user_id);
                          }}
                        >
                          <MoreVertical size={18} />
                        </button>

                        {actionMenuOpen === user.user_id && createPortal(
                          <div
                            className={`${styles.actionsDropdown} user-actions-dropdown-portal`}
                            style={{
                              position: 'fixed',
                              top: menuPosition?.top,
                              right: menuPosition?.right,
                              left: 'auto',
                              margin: 0
                            }}
                          >
                            <button
                              className={styles.actionItem}
                              onClick={() => onEdit(user)}
                              disabled={isSubmitting || !!isDeletingUser || !!isTogglingStatus}
                            >
                              <Edit2 size={16} /> {t('admin.user_management.table.actions.edit')}
                            </button>
                            <button
                              className={styles.actionItem}
                              onClick={() => {
                                onToggleStatus(user.user_id, user.is_active);
                                setActionMenuOpen(null);
                              }}
                              disabled={isTogglingStatus === user.user_id || !!isDeletingUser}
                            >
                              <RotateCw size={16} />
                              {isTogglingStatus === user.user_id
                                ? t('admin.user_management.table.actions.processing')
                                : user.is_active ? t('admin.user_management.table.actions.deactivate') : t('admin.user_management.table.actions.activate')}
                            </button>
                            <button
                              className={`${styles.actionItem} ${styles.actionItemDanger}`}
                              onClick={() => {
                                onDelete(user.user_id, user.display_name || user.email);
                                setActionMenuOpen(null);
                              }}
                              disabled={isDeletingUser === user.user_id || !!isTogglingStatus}
                            >
                              <Trash2 size={16} />
                              {isDeletingUser === user.user_id ? t('admin.user_management.table.actions.deleting') : t('admin.user_management.table.actions.delete')}
                            </button>
                          </div>,
                          document.body
                        )}
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default UserTable;
