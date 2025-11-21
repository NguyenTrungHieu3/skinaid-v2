import React, { useEffect } from 'react';
import { MoreVertical, Edit2, RotateCw, Trash2 } from 'lucide-react';
import styles from './UserTable.module.css';

interface User {
  user_id: string;
  email: string;
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
  // Close action menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (actionMenuOpen && !(event.target as Element).closest(`.${styles.actionsMenu}`)) {
        setActionMenuOpen(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
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
    const role = roles[0] || 'user';
    const roleClasses: Record<string, string> = {
      user: styles.adminBadgeGray,
      moderator: styles.adminBadgeBlue,
      admin: styles.adminBadgePurple
    };
    return roleClasses[role] || styles.adminBadgeGray;
  };

  if (loading) {
    return (
      <div className={styles.adminCard}>
        <div className={styles.adminCardContent} style={{ padding: '3rem', textAlign: 'center' }}>
          <p>Loading users...</p>
        </div>
      </div>
    );
  }

  if (users.length === 0) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>👥</div>
        <p>No users found</p>
        <p className={styles.emptySubtitle}>Try adjusting your filters</p>
      </div>
    );
  }

  return (
    <div className={styles.adminCard}>
      <div className={styles.tableContainer}>
        <table className={styles.userTable}>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Uploads</th>
              <th>Join Date</th>
              <th>Actions</th>
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
                    <span>{user.display_name || 'No Name'}</span>
                  </div>
                </td>
                <td>{user.email}</td>
                <td>
                  <span className={`${styles.adminBadge} ${getRoleBadgeClass(user.roles)}`}>
                    {user.roles[0] || 'user'}
                  </span>
                </td>
                <td>
                  <span className={`${styles.adminBadge} ${user.is_active ? styles.adminBadgeSuccess : styles.adminBadgeGray}`}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>{user.upload_count || 0}</td>
                <td>{formatDate(user.created_at)}</td>
                <td>
                  <div className={styles.actionsMenu}>
                    <button 
                      className={styles.actionsTrigger}
                      onClick={() => setActionMenuOpen(actionMenuOpen === user.user_id ? null : user.user_id)}
                    >
                      <MoreVertical size={18} />
                    </button>
                    
                    {actionMenuOpen === user.user_id && (
                      <div className={styles.actionsDropdown}>
                        <button 
                          className={styles.actionItem}
                          onClick={() => onEdit(user)}
                          disabled={isSubmitting || !!isDeletingUser || !!isTogglingStatus}
                        >
                          <Edit2 size={16} /> Edit
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
                            ? 'Processing...' 
                            : user.is_active ? 'Deactivate' : 'Activate'}
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
                          {isDeletingUser === user.user_id ? 'Deleting...' : 'Delete'}
                        </button>
                      </div>
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
