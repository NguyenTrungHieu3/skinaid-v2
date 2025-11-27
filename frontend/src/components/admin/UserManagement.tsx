import { useState, useEffect, useRef, type FC } from 'react';
import { Plus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { getUsers, createUser, updateUser, updateUserStatus, deleteUser } from '../../services/userService';
import { useToast } from '../../contexts/ToastContext';
import UserFilters from './components/UserFilters';
import UserTable from './components/UserTable';
import UserFormModal from './components/UserFormModal';
import Pagination from '../common/Pagination';
import styles from './UserManagement.module.css';

interface User {
  user_id: string;
  email: string;
  display_name: string;
  roles: string[];
  is_active: boolean;
  upload_count?: number;
  created_at: string;
}

interface UserFormData {
  email: string;
  display_name: string;
  password?: string;
  role: string;
}

interface ApiError {
  response?: {
    data?: {
      error?: string;
    };
  };
}

const UserManagement: FC = () => {
  const { t } = useTranslation();
  const toast = useToast();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Loading states for async operations
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeletingUser, setIsDeletingUser] = useState<string | null>(null);
  const [isTogglingStatus, setIsTogglingStatus] = useState<string | null>(null);

  // Pagination & Filters
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const [searchInput, setSearchInput] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');

  // Debounce timer ref
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [actionMenuOpen, setActionMenuOpen] = useState<string | null>(null);

  // Fetch users
  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await getUsers({
        page: currentPage,
        limit: 10,
        search: searchTerm,
        role: selectedRole,
        status: selectedStatus
      });

      if (response.success && response.data) {
        setUsers(response.data.users || []);
        setTotalUsers(response.data.pagination.total);
        setTotalPages(response.data.pagination.total_pages);
      }
    } catch (err: unknown) {
      const error = err as ApiError;
      console.error('Error fetching users:', error);
      setError(error.response?.data?.error || 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, searchTerm, selectedRole, selectedStatus]);

  // Debounce search input
  useEffect(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      setSearchTerm(searchInput);
      setCurrentPage(1);
    }, 500);

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [searchInput]);

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchInput(e.target.value);
  };

  // Handle role filter
  const handleRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedRole(e.target.value);
    setCurrentPage(1);
  };

  // Handle status filter
  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedStatus(e.target.value);
    setCurrentPage(1);
  };

  // Handle add user
  const handleAddUser = async (data: UserFormData) => {
    if (isSubmitting) return;

    try {
      setIsSubmitting(true);
      const response = await createUser(data);
      if (response.success) {
        setShowAddModal(false);
        fetchUsers();
        toast.success('User created successfully!');
      }
    } catch (err: unknown) {
      const error = err as ApiError;
      console.error('Error creating user:', error);
      toast.error(error.response?.data?.error || 'Failed to create user');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle edit user
  const handleEditUser = async (data: UserFormData) => {
    if (isSubmitting || !selectedUser) return;

    try {
      setIsSubmitting(true);
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { password, ...updateData } = data;
      const response = await updateUser(selectedUser.user_id, updateData);
      if (response.success) {
        setShowEditModal(false);
        setSelectedUser(null);
        fetchUsers();
        toast.success('User updated successfully!');
      }
    } catch (err: unknown) {
      const error = err as ApiError;
      console.error('Error updating user:', error);
      toast.error(error.response?.data?.error || 'Failed to update user');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle delete user
  const handleDeleteUser = async (userId: string, displayName: string) => {
    if (window.confirm(`Are you sure you want to delete user "${displayName}"?`)) {
      if (isDeletingUser) return;

      try {
        setIsDeletingUser(userId);
        const response = await deleteUser(userId);
        if (response.success) {
          fetchUsers();
          toast.success('User deleted successfully!');
        }
      } catch (err: unknown) {
        const error = err as ApiError;
        console.error('Error deleting user:', error);
        toast.error(error.response?.data?.error || 'Failed to delete user');
      } finally {
        setIsDeletingUser(null);
      }
    }
  };

  // Handle toggle status
  const handleToggleStatus = async (userId: string, currentStatus: boolean) => {
    if (isTogglingStatus) return;

    const newStatus = !currentStatus;
    try {
      setIsTogglingStatus(userId);
      const response = await updateUserStatus(userId, newStatus);
      if (response.success) {
        fetchUsers();
        toast.success(`User status updated to ${newStatus ? 'active' : 'inactive'}`);
      }
    } catch (err: unknown) {
      const error = err as ApiError;
      console.error('Error updating status:', error);
      toast.error(error.response?.data?.error || 'Failed to update status');
    } finally {
      setIsTogglingStatus(null);
    }
  };

  // Open edit modal
  const openEditModal = (user: User) => {
    setSelectedUser(user);
    setShowEditModal(true);
    setActionMenuOpen(null);
  };

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    // Use a more specific selector or ref if possible, but this works for now
    const tableElement = document.querySelector(`.${styles.userTable}`);
    if (tableElement) {
      tableElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const usersPerPage = 10;
  const indexOfFirstUser = (currentPage - 1) * usersPerPage + 1;
  const indexOfLastUser = Math.min(currentPage * usersPerPage, totalUsers);

  return (
    <div className={styles.userManagementPage}>
      {/* Header */}
      <div className={styles.adminPageHeader}>
        <div className={styles.adminPageTitle}>
          <h1>{t('admin.user_management.title')}</h1>
          <p>{t('admin.user_management.subtitle')}</p>
        </div>
        <button
          className={styles.adminBtnPrimary}
          onClick={() => setShowAddModal(true)}
        >
          <Plus size={18} strokeWidth={2.5} />
          {t('admin.user_management.add_user')}
        </button>
      </div>

      {/* Filters */}
      <UserFilters
        search={searchInput}
        onSearchChange={handleSearchChange}
        role={selectedRole}
        onRoleChange={handleRoleChange}
        status={selectedStatus}
        onStatusChange={handleStatusChange}
      />

      {/* Users count */}
      <div className={styles.usersCount}>
        {t('admin.user_management.total_users')} ({totalUsers} total)
        {totalUsers > 0 && (
          <span style={{ marginLeft: '1rem', color: '#666', fontSize: '0.9rem' }}>
            {t('admin.user_management.showing', { start: indexOfFirstUser, end: indexOfLastUser, total: totalUsers })}
          </span>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div style={{
          padding: '1rem',
          background: '#fee',
          color: '#c33',
          borderRadius: '8px',
          marginBottom: '1rem'
        }}>
          {error}
        </div>
      )}

      {/* Users Table */}
      <UserTable
        users={users}
        loading={loading}
        onEdit={openEditModal}
        onDelete={handleDeleteUser}
        onToggleStatus={handleToggleStatus}
        actionMenuOpen={actionMenuOpen}
        setActionMenuOpen={setActionMenuOpen}
        isSubmitting={isSubmitting}
        isDeletingUser={isDeletingUser}
        isTogglingStatus={isTogglingStatus}
      />

      {/* Pagination */}
      {!loading && totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          totalItems={totalUsers}
          itemsPerPage={10}
          onPageChange={handlePageChange}
          showInfo={false}
        />
      )}

      {/* Add User Modal */}
      <UserFormModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSubmit={handleAddUser}
        initialData={null}
        isEdit={false}
        isSubmitting={isSubmitting}
      />

      {/* Edit User Modal */}
      <UserFormModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        onSubmit={handleEditUser}
        initialData={selectedUser ? {
          email: selectedUser.email,
          display_name: selectedUser.display_name,
          roles: selectedUser.roles
        } : null}
        isEdit={true}
        isSubmitting={isSubmitting}
      />
    </div>
  );
};

export default UserManagement;
