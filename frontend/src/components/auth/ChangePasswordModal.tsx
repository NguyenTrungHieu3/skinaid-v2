// src/components/auth/ChangePasswordModal.tsx
import React, { useState } from "react";
import styles from "./Form.module.css"; // Dùng chung CSS với các form khác
import { FiLock, FiEye, FiEyeOff } from "react-icons/fi";
import { FaSave } from "react-icons/fa";
import {
  changePassword,
  type ChangePasswordFormData,
} from "../../services/authService";
import { isAxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../contexts/AuthContext";

interface ModalProps {
  onClose: () => void; // Hàm để đóng modal
}

// Hàm validation (bạn có thể tùy chỉnh)
const validatePasswords = (data: ChangePasswordFormData) => {
  if (data.newPassword.length < 8)
    return "Password must be at least 8 characters.";
  if (data.newPassword !== data.confirmPassword)
    return "New passwords do not match.";
  if (data.oldPassword === data.newPassword)
    return "New password must be different from the old one.";
  return "";
};

const ChangePasswordModal = ({ onClose }: ModalProps) => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState<ChangePasswordFormData>({
    oldPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  const [apiError, setApiError] = useState("");
  const [apiSuccess, setApiSuccess] = useState("");
  const [showPass, setShowPass] = useState({
    old: false,
    new: false,
    confirm: false,
  });

  const { user, logout } = useAuth(); // <-- 2. LẤY USER TỪ CONTEXT

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setApiError("");
    setApiSuccess("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError("");
    setApiSuccess("");

    // 1. Validate
    const validationError = validatePasswords(formData);
    if (validationError) {
      setApiError(validationError);
      return;
    }

    const token =
      localStorage.getItem("userToken") || sessionStorage.getItem("userToken");

    if (!token) {
      setApiError("Authentication error. Please log in again.");
      logout(); // Đăng xuất nếu không có token
      return;
    }
    // 2. Gọi API
    try {
      const response = await changePassword(formData, token);
      setApiSuccess(response.data.message || "Password updated successfully!");
      // Tự động đóng sau 2 giây
      setTimeout(() => {
        onClose();
        logout();
      }, 500);
    } catch (err) {
      if (isAxiosError(err)) {
        setApiError(err.response?.data?.message || "An error occurred.");
      } else {
        setApiError("An unknown error occurred.");
      }
    }
  };

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <h2 className={styles.formTitle}>{t("settings.password_title")}</h2>

          {apiError && <div className={styles.apiErrorMessage}>{apiError}</div>}
          {apiSuccess && (
            <div className={styles.apiSuccessMessage}>{apiSuccess}</div>
          )}

          {/* Old Password */}
          <div className={styles.formGroup}>
            <label>{t("settings.password_old")}</label>
            <div className={styles.inputWrapper}>
              <FiLock className={styles.icon} />
              <input
                type={showPass.old ? "text" : "password"}
                name="oldPassword"
                placeholder={t("placeholder.old_password")}
                value={formData.oldPassword}
                onChange={handleChange}
              />
              <span
                className={styles.togglePasswordIcon}
                onClick={() => setShowPass((p) => ({ ...p, old: !p.old }))}
              >
                {showPass.old ? <FiEye /> : <FiEyeOff />}
              </span>
            </div>
          </div>

          {/* New Password */}
          <div className={styles.formGroup}>
            <label>{t("settings.password_new")}</label>
            <div className={styles.inputWrapper}>
              <FiLock className={styles.icon} />
              <input
                type={showPass.new ? "text" : "password"}
                name="newPassword"
                placeholder={t("placeholder.new_password")}
                value={formData.newPassword}
                onChange={handleChange}
              />
              <span
                className={styles.togglePasswordIcon}
                onClick={() => setShowPass((p) => ({ ...p, new: !p.new }))}
              >
                {showPass.new ? <FiEye /> : <FiEyeOff />}
              </span>
            </div>
          </div>

          {/* Confirm New Password */}
          <div className={styles.formGroup}>
            <label>{t("settings.password_confirmNew")}</label>
            <div className={styles.inputWrapper}>
              <FiLock className={styles.icon} />
              <input
                type={showPass.confirm ? "text" : "password"}
                name="confirmPassword"
                placeholder={t("placeholder.confirmNew_password")}
                value={formData.confirmPassword}
                onChange={handleChange}
              />
              <span
                className={styles.togglePasswordIcon}
                onClick={() =>
                  setShowPass((p) => ({ ...p, confirm: !p.confirm }))
                }
              >
                {showPass.confirm ? <FiEye /> : <FiEyeOff />}
              </span>
            </div>
          </div>

          <div className={styles.modalActions}>
            <button
              type="button"
              className={styles.btnCancel}
              onClick={onClose}
            >
              {t("button.cancel")}
            </button>
            <button type="submit" className={styles.btnSave}>
              <FaSave /> {t("button.update_password")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChangePasswordModal;
