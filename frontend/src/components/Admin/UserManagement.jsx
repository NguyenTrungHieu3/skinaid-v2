import React, { useState, useEffect, useRef } from 'react';
import { FiSearch, FiMoreVertical, FiPlus, FiEdit2, FiRotateCw, FiTrash2 } from 'react-icons/fi';
import { getUsers, createUser, updateUser, updateUserStatus, deleteUser } from '../../services/UserService';
import { useToast } from '../../contexts/ToastContext';

export default function UserManagement() {
  const toast = useToast();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Loading states for async operations
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeletingUser, setIsDeletingUser] = useState(null); // Store user ID being deleted
  const [isTogglingStatus, setIsTogglingStatus] = useState(null); // Store user ID being toggled
  
  // Pagination & Filters
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const [searchInput, setSearchInput] = useState(''); // Immediate input value
  const [searchTerm, setSearchTerm] = useState(''); // Debounced search term for API
  const [selectedRole, setSelectedRole] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  
  // Debounce timer ref
  const debounceTimer = useRef(null);
  
  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [actionMenuOpen, setActionMenuOpen] = useState(null);
  
  // Form data
  const [formData, setFormData] = useState({
    email: '',
    display_name: '',
    password: '',
    role: 'user'
  });

  // Form validation errors
  const [validationErrors, setValidationErrors] = useState({});

  // Validate email format
  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Validate password strength
  const validatePassword = (password) => {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    return passwordRegex.test(password);
  };

  // Validate form fields
  const validateForm = (isEdit = false) => {
    const errors = {};

    // Email validation
    if (!formData.email || !formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      errors.email = 'Invalid email format';
    }

    // Display name validation
    if (!formData.display_name || !formData.display_name.trim()) {
      errors.display_name = 'Display name is required';
    } else if (formData.display_name.trim().length < 2) {
      errors.display_name = 'Display name must be at least 2 characters';
    } else if (formData.display_name.trim().length > 50) {
      errors.display_name = 'Display name must not exceed 50 characters';
    }

    // Password validation (only for create, not edit)
    if (!isEdit) {
      if (!formData.password || !formData.password.trim()) {
        errors.password = 'Password is required';
      } else if (!validatePassword(formData.password)) {
        errors.password = 'Password must be at least 8 characters with 1 uppercase, 1 lowercase, and 1 number';
      }
    }

    // Role validation
    if (!formData.role) {
      errors.role = 'Role is required';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

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
    } catch (err) {
      console.error('Error fetching users:', err);
      setError(err.response?.data?.error || 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, searchTerm, selectedRole, selectedStatus]);

  // Debounce search input - updates searchTerm after 500ms of no typing
  useEffect(() => {
    // Clear existing timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Set new timer
    debounceTimer.current = setTimeout(() => {
      setSearchTerm(searchInput);
      setCurrentPage(1); // Reset to first page when search changes
    }, 500);

    // Cleanup on unmount or when searchInput changes
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [searchInput]);

  // Close action menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (actionMenuOpen && !event.target.closest('.actions-menu')) {
        setActionMenuOpen(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [actionMenuOpen]);

  // Handle search input change (immediate, no API call yet)
  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchInput(value);
  };

  // Handle role filter
  const handleRoleChange = (e) => {
    setSelectedRole(e.target.value);
    setCurrentPage(1);
  };

  // Handle status filter
  const handleStatusChange = (e) => {
    setSelectedStatus(e.target.value);
    setCurrentPage(1);
  };

  // Handle add user
  const handleAddUser = async (e) => {
    e.preventDefault();
    if (isSubmitting) return; // Prevent double submission
    
    // Validate form
    if (!validateForm(false)) {
      toast.error('Please fix validation errors');
      return;
    }
    
    try {
      setIsSubmitting(true);
      const response = await createUser(formData);
      if (response.success) {
        setShowAddModal(false);
        resetForm();
        fetchUsers();
        toast.success('User created successfully!');
      }
    } catch (err) {
      console.error('Error creating user:', err);
      toast.error(err.response?.data?.error || 'Failed to create user');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle edit user
  const handleEditUser = async (e) => {
    e.preventDefault();
    if (isSubmitting) return; // Prevent double submission
    
    // Validate form (isEdit = true, so password is optional)
    if (!validateForm(true)) {
      toast.error('Please fix validation errors');
      return;
    }
    
    try {
      setIsSubmitting(true);
      const { password, ...updateData } = formData;
      const response = await updateUser(selectedUser.user_id, updateData);
      if (response.success) {
        setShowEditModal(false);
        setSelectedUser(null);
        resetForm();
        fetchUsers();
        toast.success('User updated successfully!');
      }
    } catch (err) {
      console.error('Error updating user:', err);
      toast.error(err.response?.data?.error || 'Failed to update user');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle delete user
  const handleDeleteUser = async (userId, displayName) => {
    if (window.confirm(`Are you sure you want to delete user "${displayName}"?`)) {
      if (isDeletingUser) return; // Prevent multiple deletes
      
      try {
        setIsDeletingUser(userId);
        const response = await deleteUser(userId);
        if (response.success) {
          fetchUsers();
          toast.success('User deleted successfully!');
        }
      } catch (err) {
        console.error('Error deleting user:', err);
        toast.error(err.response?.data?.error || 'Failed to delete user');
      } finally {
        setIsDeletingUser(null);
      }
    }
  };

  // Handle toggle status
  const handleToggleStatus = async (userId, currentStatus) => {
    if (isTogglingStatus) return; // Prevent multiple toggles
    
    const newStatus = !currentStatus;
    try {
      setIsTogglingStatus(userId);
      const response = await updateUserStatus(userId, newStatus);
      if (response.success) {
        fetchUsers();
        toast.success(`User status updated to ${newStatus ? 'active' : 'inactive'}`);
      }
    } catch (err) {
      console.error('Error updating status:', err);
      toast.error(err.response?.data?.error || 'Failed to update status');
    } finally {
      setIsTogglingStatus(null);
    }
  };

  // Open edit modal
  const openEditModal = (user) => {
    setSelectedUser(user);
    setFormData({
      email: user.email,
      display_name: user.display_name || '',
      password: '',
      role: user.roles[0] || 'user'
    });
    setShowEditModal(true);
    setActionMenuOpen(null);
  };

  // Reset form
  const resetForm = () => {
    setFormData({
      email: '',
      display_name: '',
      password: '',
      role: 'user'
    });
    setValidationErrors({});
  };

  // Get initials for avatar
  const getInitials = (name) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  // Format date
  const formatDate = (dateString) => {
    return new Date(dateString).toISOString().split('T')[0];
  };

  // Get role badge class
  const getRoleBadgeClass = (roles) => {
    const role = roles[0] || 'user';
    const roleClasses = {
      user: 'admin-badge-gray',
      moderator: 'admin-badge-blue',
      admin: 'admin-badge-purple'
    };
    return roleClasses[role] || 'admin-badge-gray';
  };

  // Handle page change with smooth scroll
  const handlePageChange = (page) => {
    setCurrentPage(page);
    // Smooth scroll to top of table
    document.querySelector('.user-table')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // Get page numbers to display with ellipsis
  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 5;

    if (totalPages <= maxPagesToShow) {
      // Show all pages if total is small
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Show first, last, and pages around current
      if (currentPage <= 3) {
        // Near the start
        for (let i = 1; i <= 4; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        // Near the end
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 3; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        // In the middle
        pages.push(1);
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      }
    }

    return pages;
  };

  // Calculate displayed items range
  const usersPerPage = 10;
  const indexOfFirstUser = (currentPage - 1) * usersPerPage + 1;
  const indexOfLastUser = Math.min(currentPage * usersPerPage, totalUsers);

  return (
    <div className="admin-space-y-6">
      {/* Header */}
      <div className="admin-page-header">
        <div className="admin-page-title">
          <h1>User Management</h1>
          <p>Manage user accounts and permissions</p>
        </div>
        <button 
          className="admin-btn-primary"
          onClick={() => {
            resetForm();
            setShowAddModal(true);
          }}
        >
          <FiPlus size={18} strokeWidth={2.5} />
          Add New User
        </button>
      </div>

      {/* Filters */}
      <div className="admin-card">
        <div className="user-filters">
          <div className="search-box">
            <FiSearch className="search-icon" size={18} />
            <input
              type="text"
              placeholder="Search users by name or email..."
              value={searchInput}
              onChange={handleSearchChange}
            />
          </div>
          
          <select 
            className="filter-select"
            value={selectedRole}
            onChange={handleRoleChange}
          >
            <option value="">All Roles</option>
            <option value="user">User</option>
            <option value="moderator">Moderator</option>
            <option value="admin">Admin</option>
          </select>

          <select 
            className="filter-select"
            value={selectedStatus}
            onChange={handleStatusChange}
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Users count */}
      <div className="users-count">
        Users ({totalUsers} total)
        {totalUsers > 0 && (
          <span className="page-info" style={{ marginLeft: '1rem', color: '#666', fontSize: '0.9rem' }}>
            Showing {indexOfFirstUser}-{indexOfLastUser} of {totalUsers}
          </span>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="error-message" style={{ 
          padding: '1rem', 
          background: '#fee', 
          color: '#c33', 
          borderRadius: '8px' 
        }}>
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div className="admin-card">
          <div className="admin-card-content" style={{ padding: '3rem', textAlign: 'center' }}>
            <p>Loading users...</p>
          </div>
        </div>
      ) : (
        <>
          {/* Users Table */}
          {users.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">👥</div>
              <p>No users found</p>
              <p className="empty-subtitle">Try adjusting your filters or search terms</p>
            </div>
          ) : (
            <>
              <div className="admin-card">
                <div className="table-container">
                  <table className="user-table">
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
                          <div className="user-info">
                            <div className="user-avatar">
                              {getInitials(user.display_name || user.email)}
                            </div>
                            <span>{user.display_name || 'No name'}</span>
                          </div>
                        </td>
                        <td>{user.email}</td>
                        <td>
                          <span className={`admin-badge ${getRoleBadgeClass(user.roles)}`}>
                            {user.roles[0] || 'user'}
                          </span>
                        </td>
                        <td>
                          <span className={`admin-badge ${user.is_active ? 'admin-badge-success' : 'admin-badge-gray'}`}>
                            {user.is_active ? 'active' : 'inactive'}
                          </span>
                        </td>
                        <td>{user.upload_count || 0}</td>
                        <td>{formatDate(user.created_at)}</td>
                        <td>
                          <div className="actions-menu">
                            <button 
                              className="actions-trigger"
                              onClick={() => setActionMenuOpen(actionMenuOpen === user.user_id ? null : user.user_id)}
                            >
                              <FiMoreVertical size={18} />
                            </button>
                            
                            {actionMenuOpen === user.user_id && (
                              <div className="actions-dropdown">
                                <button 
                                  className="action-item"
                                  onClick={() => openEditModal(user)}
                                  disabled={isSubmitting || isDeletingUser || isTogglingStatus}
                                >
                                  <FiEdit2 size={16} /> Edit
                                </button>
                                <button 
                                  className="action-item"
                                  onClick={() => {
                                    handleToggleStatus(user.user_id, user.is_active);
                                    setActionMenuOpen(null);
                                  }}
                                  disabled={isTogglingStatus === user.user_id || isDeletingUser}
                                >
                                  <FiRotateCw size={16} /> 
                                  {isTogglingStatus === user.user_id 
                                    ? 'Processing...' 
                                    : user.is_active ? 'Deactivate' : 'Activate'}
                                </button>
                                <button 
                                  className="action-item danger"
                                  onClick={() => {
                                    handleDeleteUser(user.user_id, user.display_name || user.email);
                                    setActionMenuOpen(null);
                                  }}
                                  disabled={isDeletingUser === user.user_id || isTogglingStatus}
                                >
                                  <FiTrash2 size={16} /> 
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

            {/* Pagination */}
            {totalPages > 1 && (
            <div className="pagination">
              <button 
                className="pagination-btn"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
              >
                Previous
              </button>
              
              <div className="pagination-numbers">
                {getPageNumbers().map((page, index) => (
                  page === '...' ? (
                    <span key={`ellipsis-${index}`} className="pagination-ellipsis">
                      ...
                    </span>
                  ) : (
                    <button
                      key={page}
                      onClick={() => handlePageChange(page)}
                      className={`pagination-number ${currentPage === page ? 'active' : ''}`}
                    >
                      {page}
                    </button>
                  )
                ))}
              </div>
              
              <button 
                className="pagination-btn"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                Next
              </button>
            </div>
          )}
          </>
        )}
      </>
      )}

      {/* Add User Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Add New User</h2>
              <button className="close-btn" onClick={() => setShowAddModal(false)}>×</button>
            </div>
            
            <form onSubmit={handleAddUser}>
              <div className="form-group">
                <label>Email *</label>
                <input 
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => {
                    setFormData({...formData, email: e.target.value});
                    if (validationErrors.email) {
                      setValidationErrors({...validationErrors, email: ''});
                    }
                  }}
                  className={validationErrors.email ? 'error' : ''}
                />
                {validationErrors.email && (
                  <span className="error-message">{validationErrors.email}</span>
                )}
              </div>

              <div className="form-group">
                <label>Display Name *</label>
                <input 
                  type="text"
                  required
                  value={formData.display_name}
                  onChange={(e) => {
                    setFormData({...formData, display_name: e.target.value});
                    if (validationErrors.display_name) {
                      setValidationErrors({...validationErrors, display_name: ''});
                    }
                  }}
                  className={validationErrors.display_name ? 'error' : ''}
                />
                {validationErrors.display_name && (
                  <span className="error-message">{validationErrors.display_name}</span>
                )}
              </div>

              <div className="form-group">
                <label>Password *</label>
                <input 
                  type="password"
                  required
                  minLength="8"
                  value={formData.password}
                  onChange={(e) => {
                    setFormData({...formData, password: e.target.value});
                    if (validationErrors.password) {
                      setValidationErrors({...validationErrors, password: ''});
                    }
                  }}
                  className={validationErrors.password ? 'error' : ''}
                />
                {validationErrors.password && (
                  <span className="error-message">{validationErrors.password}</span>
                )}
                <small style={{ display: 'block', marginTop: '4px', color: '#666' }}>
                  At least 8 characters with 1 uppercase, 1 lowercase, and 1 number
                </small>
              </div>

              <div className="form-group">
                <label>Role</label>
                <select 
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value})}
                >
                  <option value="user">User</option>
                  <option value="moderator">Moderator</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              <div className="modal-actions">
                <button 
                  type="button" 
                  className="btn-secondary" 
                  onClick={() => setShowAddModal(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="admin-btn-primary"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Creating...' : 'Create User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit User</h2>
              <button className="close-btn" onClick={() => setShowEditModal(false)}>×</button>
            </div>
            
            <form onSubmit={handleEditUser}>
              <div className="form-group">
                <label>Email *</label>
                <input 
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => {
                    setFormData({...formData, email: e.target.value});
                    if (validationErrors.email) {
                      setValidationErrors({...validationErrors, email: ''});
                    }
                  }}
                  className={validationErrors.email ? 'error' : ''}
                />
                {validationErrors.email && (
                  <span className="error-message">{validationErrors.email}</span>
                )}
              </div>

              <div className="form-group">
                <label>Display Name *</label>
                <input 
                  type="text"
                  required
                  value={formData.display_name}
                  onChange={(e) => {
                    setFormData({...formData, display_name: e.target.value});
                    if (validationErrors.display_name) {
                      setValidationErrors({...validationErrors, display_name: ''});
                    }
                  }}
                  className={validationErrors.display_name ? 'error' : ''}
                />
                {validationErrors.display_name && (
                  <span className="error-message">{validationErrors.display_name}</span>
                )}
              </div>

              <div className="form-group">
                <label>Role</label>
                <select 
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value})}
                >
                  <option value="user">User</option>
                  <option value="moderator">Moderator</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              <div className="modal-actions">
                <button 
                  type="button" 
                  className="btn-secondary" 
                  onClick={() => setShowEditModal(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="admin-btn-primary"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Updating...' : 'Update User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
