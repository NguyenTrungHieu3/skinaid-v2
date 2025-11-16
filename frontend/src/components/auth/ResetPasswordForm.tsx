// src/components/auth/ResetPasswordForm.tsx

import styles from "./Form.module.css";
import { FiLock, FiEye, FiEyeOff } from "react-icons/fi";
import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { confirmPasswordReset } from "../../services/authService";
import { isAxiosError } from "axios";

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
  allValues: ResetPasswordFormData
): string => {
  switch (name) {
    case "password":
      if (value.trim() === "") {
        return "Password is required";
      }
      if (value.length < 8) {
        return "Password must be at least 8 characters.";
      }
      if (!/[A-Z]/.test(value)) {
        return "Password must contain at least one uppercase letter.";
      }
      if (!/[0-9]/.test(value)) {
        return "Password must contain at least one number.";
      }
      if (!/[!@#$%^&*]/.test(value)) {
        return "Password must contain at least one special character (!@#$%^&*).";
      }
      return "";
    case "confirmPassword":
      if (value.trim() === "") {
        return "Confirm Password is required.";
      }
      if (value !== allValues.password) {
        return "Passwords do not match.";
      }
      return "";
    default:
      return "";
  }
};

const ResetPasswordForm = () => {
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
    const errorMessage = validateField(name, value, currentFormData);
    setErrors((prev) => ({ ...prev, [name]: errorMessage }));

    if (name === "password" && formData.confirmPassword) {
      const confirmError = validateField(
        "confirmPassword",
        formData.confirmPassword,
        currentFormData
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
      formData
    );
    const confirmPasswordError = validateField(
      "confirmPassword",
      formData.confirmPassword,
      formData
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
      <h2 className={styles.formTitle}>Reset Password</h2>
      <p className={styles.formSubtitle}>Please enter your new password.</p>

      {apiError && <div className={styles.apiErrorMessage}>{apiError}</div>}
      {apiSuccess && (
        <div className={styles.apiSuccessMessage}>{apiSuccess}</div>
      )}

      {/* Password */}
      <div className={styles.formGroup}>
        <label>New password</label>
        <div className={styles.inputWrapper}>
          <FiLock className={styles.icon} />
          <input
            type={showPassword ? "text" : "password"}
            name="password"
            placeholder="Enter new password"
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
        <label>Confirm password</label>
        <div className={styles.inputWrapper}>
          <FiLock className={styles.icon} />
          <input
            type={showConfirmPassword ? "text" : "password"}
            name="confirmPassword"
            placeholder="Confirm new password"
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
        {apiSuccess ? "Updated!" : "Update Password"}
      </button>
    </form>
  );
};

export default ResetPasswordForm;
