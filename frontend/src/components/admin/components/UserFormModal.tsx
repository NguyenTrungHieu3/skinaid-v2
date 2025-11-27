import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
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
      errors.email = t('admin.user_management.form.errors.email_required');
    } else if (!validateEmail(formData.email)) {
      errors.email = t('admin.user_management.form.errors.email_invalid');
    }

    if (!formData.display_name || !formData.display_name.trim()) {
      errors.display_name = t('admin.user_management.form.errors.name_required');
    } else if (formData.display_name.trim().length < 2) {
      errors.display_name = t('admin.user_management.form.errors.name_min');
    } else if (formData.display_name.trim().length > 50) {
      errors.display_name = t('admin.user_management.form.errors.name_max');
    }

    if (!isEdit) {
      if (!formData.password || !formData.password.trim()) {
        errors.password = t('admin.user_management.form.errors.password_required');
      } else if (!validatePassword(formData.password)) {
        errors.password = t('admin.user_management.form.errors.password_invalid');
      }
    }

    if (!formData.role) {
      errors.role = t('admin.user_management.form.errors.role_required');
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
          <h2>{isEdit ? t('admin.user_management.form.title_edit') : t('admin.user_management.form.title_add')}</h2>
          <button className={styles.closeBtn} onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Username */}
          <div className={styles.formGroup}>
            <label>{t('admin.user_management.form.labels.username')} *</label>
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

          {/* Password - only for new users */}
          {!isEdit && (
            <div className={styles.formGroup}>
              <label>{t('admin.user_management.form.labels.password')} *</label>
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
                {t('admin.user_management.form.password_hint')}
              </small>
            </div>
          )}

          {/* Email */}
          <div className={styles.formGroup}>
            <label>{t('admin.user_management.form.labels.email')} *</label>
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

          {/* Role */}
          <div className={styles.formGroup}>
            <label>{t('admin.user_management.form.labels.role')}</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            >
              <option value="user">{t('admin.user_management.roles.user')}</option>
              <option value="admin">{t('admin.user_management.roles.admin')}</option>
            </select>
          </div>

          <div className={styles.modalActions}>
            <button
              type="button"
              className={styles.btnSecondary}
              onClick={onClose}
              disabled={isSubmitting}
            >
              {t('admin.user_management.form.buttons.cancel')}
            </button>
            <button
              type="submit"
              className={styles.adminBtnPrimary}
              disabled={isSubmitting}
            >
              {isSubmitting
                ? (isEdit ? t('admin.user_management.form.buttons.updating') : t('admin.user_management.form.buttons.creating'))
                : (isEdit ? t('admin.user_management.form.buttons.update') : t('admin.user_management.form.buttons.create'))}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UserFormModal;
