import { Link, useNavigate } from "react-router-dom";
import styles from "./Form.module.css";
import { FaRegUser } from "react-icons/fa";
import { FiLock, FiEye, FiEyeOff } from "react-icons/fi";
import React, { useState } from "react";
import { loginUser } from "../../services/authService";
import { isAxiosError } from "axios";
import { useAuth } from "../../contexts/AuthContext";
import { useTranslation } from "react-i18next";

export type LoginFormData = {
  username: string;
  password: string;
};

// 1. Tách logic validation ra 1 hàm riêng để tái sử dụng (nếu cần)
const validateField = (
  name: string,
  value: string,
  t: (key: string) => string
): string => {
  switch (name) {
    case "username":
      if (value.trim() === "") {
        return t("validation.error_username_required");
      }
      return "";
    case "password":
      if (value.trim() === "") {
        return t("validation.error_password_required");
      }
      return "";
    default:
      return "";
  }
};

const LoginForm = () => {
  const { t } = useTranslation();

  // Gộp state của form lại cho dễ quản lí
  const [formData, setFormData] = useState<LoginFormData>({
    username: "",
    password: "",
  });

  const [errors, setErrors] = useState({
    username: "",
    password: "",
  });

  const [showPassword, setShowPassword] = useState(false);

  // Thêm state mới cho lỗi từ API
  const [apiError, setApiError] = useState("");

  // Lưu trạng thái của checkbox "Remember me"
  const [rememberMe, setRememberMe] = useState(false);

  // Tạo hook
  const navigate = useNavigate();

  // Lấy hàm login từ context
  const { login } = useAuth();

  // Hàm này chạy khi người dùng nhập dữ liệu
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;

    // --- Cập nhật giá trị vào state ---
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));

    // --- Tự động mất lỗi ---
    if (errors[name as keyof typeof errors]) {
      setErrors((prevErrors) => ({
        ...prevErrors,
        [name]: "",
      }));
    }

    // Nếu người dùng bắt đầu gõ , xóa lỗi API cũ đi
    if (apiError) {
      setApiError("");
    }
  };

  // 4. Hàm này chạy khi người dùng click ra ngoài
  const handleBlur = (event: React.FocusEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    //Chạy validation cho riêng trường đó
    const errorMessage = validateField(name, value, t);
    //Cập nhật lỗi (nếu có)
    setErrors((prevErrors) => ({
      ...prevErrors,
      [name]: errorMessage,
    }));
  };

  // 5. Hàm này chạy khi BẤM NÚT SUBMIT
  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    // Chay validation cho tất cả các trường 1 lần cuối
    const usernameError = validateField("username", formData.username, t);
    const passwordError = validateField("password", formData.password, t);

    // Nếu có bất kì lỗi nào , hiển thị ra và dừng lại
    if (usernameError || passwordError) {
      setErrors({
        username: usernameError,
        password: passwordError,
      });
      return;
    }

    // Nếu không có lỗi, tiến hành submit form (gửi API, chuyển trang, etc)
    console.log("Form submitted", formData);

    loginUser(formData)
      .then((response) => {
        // Debug: Log toàn bộ response
        console.log("🔍 Full login response:", response.data);

        // Đăng nhập thành công , API trả vè token
        const token = response.data.data.access_token;
        const userObject = response.data.data.user;

        // Debug: Kiểm tra user object
        console.log("🔍 User object:", userObject);
        console.log("🔍 User roles:", userObject.roles);

        // --- THAY ĐỔI LỚN ---
        // Thay vì tự lưu token, hãy gọi hàm login từ context
        login(
          token,
          { ...userObject, created_at: new Date().toISOString() },
          rememberMe
        );

        // Redirect based on user role
        const userRoles = userObject.roles || [];
        console.log("🔍 Checking roles:", userRoles);

        const isAdmin = userRoles.some((role: string) => {
          const isAdminRole = role.toLowerCase() === "admin";
          console.log(`🔍 Checking role "${role}": ${isAdminRole}`);
          return isAdminRole;
        });

        console.log("🔍 Is admin?", isAdmin);

        // Chuyển hướng dựa trên role
        if (isAdmin) {
          console.log("✅ Admin user detected, redirecting to /admin");
          navigate("/admin", { replace: true });
        } else {
          console.log("✅ Regular user detected, redirecting to /");
          navigate("/", { replace: true });
        }
      })
      .catch((error) => {
        if (isAxiosError(error)) {
          if (
            error.response &&
            error.response.data &&
            error.response.data.message
          ) {
            setApiError(error.response.data.message); // "Tài khoản hoặc mật khẩu không chính xác."
          } else {
            setApiError("Something went wrong. Please try again.");
          }
        } else {
          console.error(error);
          setApiError("An unknown error occurred");
        }
      });
  };

  return (
    <form onSubmit={handleSubmit} noValidate>
      <title>{t("title.login_page")}</title>
      {/* <meta name="description" content={t("home_page.hero_desc")} /> */}

      <div className={styles.formGroup}>
        {/* Hiển thị lỗi API ngay trên dưới form */}
        {apiError && <div className={styles.apiErrorMessage}>{apiError}</div>}
        <label>{t("auth_page.username")}</label>

        <div className={styles.inputWrapper}>
          <FaRegUser className={styles.icon} />
          <input
            type="text"
            name="username" // Quan trọng : Thêm name
            placeholder={t("auth_page.username_placeholder")}
            value={formData.username}
            onChange={handleChange}
            onBlur={handleBlur}
            className={errors.username ? styles.inputError : ""}
          />
        </div>

        {errors.username && (
          <p className={styles.errorMessage}>{errors.username}</p>
        )}
      </div>

      <div className={styles.formGroup}>
        <label>{t("auth_page.password")}</label>
        <div className={styles.inputWrapper}>
          <FiLock className={styles.icon} />
          <input
            type={showPassword ? "text" : "password"}
            name="password" // Quan trọng : Thêm name
            placeholder={t("auth_page.password_placeholder")}
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
      <div className={styles.optionsRow}>
        {/* <div className={styles.radioGroup}>
          <input type="radio" id="male" name="gender" value="male" />
          <label htmlFor="male">Male</label>
          <input type="radio" id="female" name="gender" value="female" />
          <label htmlFor="female">Female</label>
        </div> */}
        <div className={styles.rememberMeGroup}>
          <input
            type="checkbox"
            id="remember"
            name="remember"
            checked={rememberMe}
            onChange={(e) => setRememberMe(e.target.checked)}
          />
          <label htmlFor="remember">{t("auth_page.remember_me")}</label>
        </div>
        <Link to="/forgot-password" className={styles.forgotLink}>
          {t("auth_page.forgot_password")}
        </Link>
      </div>
      <button type="submit" className={styles.submitButton}>
        {t("auth_page.login_button")}
      </button>
    </form>
  );
};

export default LoginForm;
