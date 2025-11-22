import React, { useState, useEffect } from 'react';
import styles from './UserFormModal.module.css';

interface UserFormData {
  email: string;
  display_name: string;
  password?: string;
  role: string;
}

interface UserFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: UserFormData) => void;
  initialData: any | null;
  isEdit: boolean;
  isSubmitting: boolean;
}

const UserFormModal: React.FC<UserFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  isEdit,
  isSubmitting
}) => {
  const [formData, setFormData] = useState<UserFormData>({
    email: '',
    display_name: '',
    password: '',
    role: 'user'
  });
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isOpen && initialData) {
      setFormData({
        email: initialData.email || '',
        display_name: initialData.display_name || '',
        password: '', // Password always empty on edit
        role: initialData.roles ? initialData.roles[0] : 'user'
      });
      setValidationErrors({});
    } else if (isOpen && !initialData) {
      // Reset for add mode
      setFormData({
        email: '',
        display_name: '',
        password: '',
        role: 'user'
      });
      setValidationErrors({});
    }
  }, [isOpen, initialData]);

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePassword = (password: string) => {
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    return passwordRegex.test(password);
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!formData.email || !formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      errors.email = 'Invalid email format';
    }

    if (!formData.display_name || !formData.display_name.trim()) {
      errors.display_name = 'Display name is required';
    } else if (formData.display_name.trim().length < 2) {
      errors.display_name = 'Display name must be at least 2 characters';
    } else if (formData.display_name.trim().length > 50) {
      errors.display_name = 'Display name must not exceed 50 characters';
    }

    if (!isEdit) {
      if (!formData.password || !formData.password.trim()) {
        errors.password = 'Password is required';
      } else if (!validatePassword(formData.password)) {
        errors.password = 'Password must be at least 8 characters with 1 uppercase, 1 lowercase, and 1 number';
      }
    }

    if (!formData.role) {
      errors.role = 'Role is required';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2>{isEdit ? 'Edit User' : 'Add New User'}</h2>
          <button className={styles.closeBtn} onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label>Email *</label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => {
                setFormData({ ...formData, email: e.target.value });
                if (validationErrors.email) {
                  setValidationErrors({ ...validationErrors, email: '' });
                }
              }}
              className={validationErrors.email ? styles.error : ''}
            />
            {validationErrors.email && (
              <span className={styles.errorMessage}>{validationErrors.email}</span>
            )}
          </div>

          <div className={styles.formGroup}>
            <label>Display Name *</label>
            <input
              type="text"
              required
              value={formData.display_name}
              onChange={(e) => {
                setFormData({ ...formData, display_name: e.target.value });
                if (validationErrors.display_name) {
                  setValidationErrors({ ...validationErrors, display_name: '' });
                }
              }}
              className={validationErrors.display_name ? styles.error : ''}
            />
            {validationErrors.display_name && (
              <span className={styles.errorMessage}>{validationErrors.display_name}</span>
            )}
          </div>

          {!isEdit && (
            <div className={styles.formGroup}>
              <label>Password *</label>
              <input
                type="password"
                required
                minLength={8}
                value={formData.password}
                onChange={(e) => {
                  setFormData({ ...formData, password: e.target.value });
                  if (validationErrors.password) {
                    setValidationErrors({ ...validationErrors, password: '' });
                  }
                }}
                className={validationErrors.password ? styles.error : ''}
              />
              {validationErrors.password && (
                <span className={styles.errorMessage}>{validationErrors.password}</span>
              )}
              <small style={{ display: 'block', marginTop: '4px', color: '#666' }}>
                At least 8 characters with 1 uppercase, 1 lowercase, and 1 number
              </small>
            </div>
          )}

          <div className={styles.formGroup}>
            <label>Role</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            >
              <option value="user">User</option>
              <option value="moderator">Moderator</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div className={styles.modalActions}>
            <button
              type="button"
              className={styles.btnSecondary}
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={styles.adminBtnPrimary}
              disabled={isSubmitting}
            >
              {isSubmitting ? (isEdit ? 'Updating...' : 'Creating...') : (isEdit ? 'Update User' : 'Create User')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UserFormModal;
