import React, { useState, useEffect } from 'react';
import { getUsers, createUser, updateUser, updateUserStatus, deleteUser } from '../../services/UserService';

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Pagination & Filters
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  
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

  // Handle search with debounce
  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchTerm(value);
    setCurrentPage(1); // Reset to first page
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
    try {
      const response = await createUser(formData);
      if (response.success) {
        setShowAddModal(false);
        resetForm();
        fetchUsers();
        alert('User created successfully!');
      }
    } catch (err) {
      console.error('Error creating user:', err);
      alert(err.response?.data?.error || 'Failed to create user');
    }
  };

  // Handle edit user
  const handleEditUser = async (e) => {
    e.preventDefault();
    try {
      const { password, ...updateData } = formData;
      const response = await updateUser(selectedUser.user_id, updateData);
      if (response.success) {
        setShowEditModal(false);
        setSelectedUser(null);
        resetForm();
        fetchUsers();
        alert('User updated successfully!');
      }
    } catch (err) {
      console.error('Error updating user:', err);
      alert(err.response?.data?.error || 'Failed to update user');
    }
  };

  // Handle delete user
  const handleDeleteUser = async (userId, displayName) => {
    if (window.confirm(`Are you sure you want to delete user "${displayName}"?`)) {
      try {
        const response = await deleteUser(userId);
        if (response.success) {
          fetchUsers();
          alert('User deleted successfully!');
        }
      } catch (err) {
        console.error('Error deleting user:', err);
        alert(err.response?.data?.error || 'Failed to delete user');
      }
    }
  };

  // Handle toggle status
  const handleToggleStatus = async (userId, currentStatus) => {
    const newStatus = !currentStatus;
    try {
      const response = await updateUserStatus(userId, newStatus);
      if (response.success) {
        fetchUsers();
      }
    } catch (err) {
      console.error('Error updating status:', err);
      alert(err.response?.data?.error || 'Failed to update status');
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
          <span style={{ marginRight: '8px' }}>+</span>
          Add New User
        </button>
      </div>

      {/* Filters */}
      <div className="admin-card">
        <div className="user-filters">
          <div className="search-box">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Search users by name or email..."
              value={searchTerm}
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
        Users ({totalUsers})
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
                  {users.length === 0 ? (
                    <tr>
                      <td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>
                        No users found
                      </td>
                    </tr>
                  ) : (
                    users.map(user => (
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
                              ⋮
                            </button>
                            
                            {actionMenuOpen === user.user_id && (
                              <div className="actions-dropdown">
                                <button 
                                  className="action-item"
                                  onClick={() => openEditModal(user)}
                                >
                                  <span>✏️</span> Edit
                                </button>
                                <button 
                                  className="action-item"
                                  onClick={() => {
                                    handleToggleStatus(user.user_id, user.is_active);
                                    setActionMenuOpen(null);
                                  }}
                                >
                                  <span>🔄</span> {user.is_active ? 'Deactivate' : 'Activate'}
                                </button>
                                <button 
                                  className="action-item danger"
                                  onClick={() => {
                                    handleDeleteUser(user.user_id, user.display_name || user.email);
                                    setActionMenuOpen(null);
                                  }}
                                >
                                  <span>🗑️</span> Delete
                                </button>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button 
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </button>
              <span>Page {currentPage} of {totalPages}</span>
              <button 
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Next
              </button>
            </div>
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
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>Display Name *</label>
                <input 
                  type="text"
                  required
                  value={formData.display_name}
                  onChange={(e) => setFormData({...formData, display_name: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>Password *</label>
                <input 
                  type="password"
                  required
                  minLength="6"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                />
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
                <button type="button" className="btn-secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="admin-btn-primary">
                  Create User
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
                <label>Email</label>
                <input 
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>Display Name</label>
                <input 
                  type="text"
                  value={formData.display_name}
                  onChange={(e) => setFormData({...formData, display_name: e.target.value})}
                />
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
                <button type="button" className="btn-secondary" onClick={() => setShowEditModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="admin-btn-primary">
                  Update User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
