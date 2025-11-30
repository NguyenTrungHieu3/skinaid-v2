// src/components/auth/ResetPasswordForm.tsx

import styles from "./Form.module.css";
import { FiLock, FiEye, FiEyeOff } from "react-icons/fi";
import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { confirmPasswordReset } from "../../services/authService";
import { isAxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { FaArrowLeft } from "react-icons/fa";

//Export type
export type ResetPasswordFormData = {
  email: string;
  password: string;
  confirmPassword: string;
};

// Hàm validation
const validateField = (
  name: string,
  value: any,
  allValues: ResetPasswordFormData,
  t: (key: string) => string
): string => {
  switch (name) {
    case "password":
      if (value.trim() === "") {
        return t("validation.error_password_required");
      }
      if (value.length < 8) {
        return t("validation.error_password_less_than_8");
      }
      if (!/[A-Z]/.test(value)) {
        return t("validation.error_password_uppercase");
      }
      if (!/[0-9]/.test(value)) {
        return t("validation.error_password_one_number");
      }
      if (!/[!@#$%^&*]/.test(value)) {
        return t("validation.error_password_special_character");
      }
      return "";
    case "confirmPassword":
      if (value.trim() === "") {
        return t("validation.error_confirm_password_required");
      }
      if (value !== allValues.password) {
        return t("validation.error_confirm_password_not_match");
      }
      return "";
    default:
      return "";
  }
};

const ResetPasswordForm = () => {
  const { t } = useTranslation();

  // Lấy token từ url
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const email = searchParams.get("email");

  const [formData, setFormData] = useState<ResetPasswordFormData>({
    email: email || "",
    password: "",
    confirmPassword: "",
  });

  const [errors, setErrors] = useState({
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [apiError, setApiError] = useState("");
  const [apiSuccess, setApiSuccess] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const navigate = useNavigate();

  // HandleChange và handleBlur
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (errors[name as keyof typeof errors]) {
      setErrors((prev) => ({
        ...prev,
        [name]: "",
      }));
    }
    if (apiError) setApiError("");
  };

  const handleBlur = (event: React.FocusEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    const currentFormData = { ...formData, [name]: value };
    const errorMessage = validateField(name, value, currentFormData, t);
    setErrors((prev) => ({ ...prev, [name]: errorMessage }));

    if (name === "password" && formData.confirmPassword) {
      const confirmError = validateField(
        "confirmPassword",
        formData.confirmPassword,
        currentFormData,
        t
      );
      setErrors((prev) => ({ ...prev, confirmPassword: confirmError }));
    }
  };

  // handleSubmit
  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setApiError("");
    setApiSuccess("");

    // Kiểm tra xem token có tồn tại trên URL không
    if (!token || !formData.email) {
      setApiError(
        "Token or Email is invalid or missing. Please try again from email."
      );
      return;
    }

    // Validate tất cả các trường
    const passwordError = validateField(
      "password",
      formData.password,
      formData,
      t
    );
    const confirmPasswordError = validateField(
      "confirmPassword",
      formData.confirmPassword,
      formData,
      t
    );

    if (passwordError || confirmPasswordError) {
      setErrors({
        email: "",
        password: passwordError,
        confirmPassword: confirmPasswordError,
      });
      return;
    }

    // Gọi API
    confirmPasswordReset(formData, token)
      .then((response) => {
        setApiSuccess(response.data.message); // Mật khẩu đã được cập nhật
        // Tùy chọn : chuyển về trang login sau 1.5 giây
        setTimeout(() => {
          navigate("/login");
        }, 1500);
      })
      .catch((err) => {
        if (isAxiosError(err)) {
          // Hiển thị lỗi từ backend
          setApiError(err.response?.data?.message || "An error occurred.");
        } else {
          setApiError("An unknown error occurred.");
        }
      });
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <title>{t("title.reset_password_page")}</title>
      <h2 className={styles.formTitle}>
        {t("auth_page.reset_password_title")}
      </h2>
      <p className={styles.formSubtitle}>
        {t("auth_page.reset_password_subtitle")}
      </p>

      {apiError && <div className={styles.apiErrorMessage}>{apiError}</div>}
      {apiSuccess && (
        <div className={styles.apiSuccessMessage}>{apiSuccess}</div>
      )}

      {/* Password */}
      <div className={styles.formGroup}>
        <label>{t("auth_page.reset_password_new")}</label>
        <div className={styles.inputWrapper}>
          <FiLock className={styles.icon} />
          <input
            type={showPassword ? "text" : "password"}
            name="password"
            placeholder={t("auth_page.reset_new_password_placeholder")}
            value={formData.password}
            onChange={handleChange}
            onBlur={handleBlur}
            className={errors.password ? styles.inputError : ""}
          />
          <span
            className={styles.togglePasswordIcon}
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? <FiEye /> : <FiEyeOff />}
          </span>
        </div>
        {errors.password && (
          <p className={styles.errorMessage}>{errors.password}</p>
        )}
      </div>

      {/* Confirm Password */}
      <div className={styles.formGroup}>
        <label>{t("auth_page.reset_password_confirm")}</label>
        <div className={styles.inputWrapper}>
          <FiLock className={styles.icon} />
          <input
            type={showConfirmPassword ? "text" : "password"}
            name="confirmPassword"
            placeholder={t("auth_page.reset_confirm_password_placeholder")}
            value={formData.confirmPassword}
            onChange={handleChange}
            onBlur={handleBlur}
            className={errors.confirmPassword ? styles.inputError : ""}
          />
          <span
            className={styles.togglePasswordIcon}
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
          >
            {showConfirmPassword ? <FiEye /> : <FiEyeOff />}
          </span>
        </div>
        {errors.confirmPassword && (
          <p className={styles.errorMessage}>{errors.confirmPassword}</p>
        )}
      </div>

      <button
        type="submit"
        className={styles.submitButton}
        disabled={!!apiSuccess}
      >
        {apiSuccess
          ? t("auth_page.reset_password_button_sub")
          : t("auth_page.reset_password_button")}
      </button>

      {/* Back to Login Link */}
      <div className={styles.backLinkWrapper}>
        <Link to="/login" className={styles.backLink}>
          <FaArrowLeft />
          <span>{t("auth_page.forgot_password_back_to_login")}</span>
        </Link>
      </div>
    </form>
  );
};

export default ResetPasswordForm;
