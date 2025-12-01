import { Link, useNavigate } from "react-router-dom";
import styles from "./Form.module.css";
import { FaRegUser } from "react-icons/fa";
import { FiLock, FiEye, FiEyeOff } from "react-icons/fi";
import React, { useState } from "react";
import { loginUser } from "../../services/authService";
import { isAxiosError } from "axios";
import { useAuth } from "../../contexts/AuthContext";

export type LoginFormData = {
  username: string;
  password: string;
};

// 1. Tách logic validation ra 1 hàm riêng để tái sử dụng (nếu cần)
const validateField = (name: string, value: string): string => {
  switch (name) {
    case "username":
      if (value.trim() === "") {
        return "Username is required";
      }
      return "";
    case "password":
      if (value.trim() === "") {
        return "Password is required";
      }
      return "";
    default:
      return "";
  }
};

const LoginForm = () => {
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
    const errorMessage = validateField(name, value);
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
    const usernameError = validateField("username", formData.username);
    const passwordError = validateField("password", formData.password);

    // Nếu có bất kì lỗi nào , hiển thị ra và dừng lại
    if (usernameError || passwordError) {
      setErrors({
        username: usernameError,
        password: passwordError,
      });
      return;
    }

    // Nếu không có lỗi, tiến hành submit form
    loginUser(formData)
      .then((response) => {
        // Đăng nhập thành công, API trả về token
        const token = response.data.data.access_token;
        const userObject = response.data.data.user;

        // Gọi hàm login từ context
        login(
          token,
          { ...userObject, created_at: new Date().toISOString() },
          rememberMe
        );

        // Redirect based on user role
        const userRoles = userObject.roles || [];
        const isAdmin = userRoles.some((role: string) => 
          role.toLowerCase() === 'admin'
        );
        
        // Chuyển hướng dựa trên role
        if (isAdmin) {
          navigate('/admin', { replace: true });
        } else {
          navigate('/', { replace: true });
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
      <div className={styles.formGroup}>
        {/* Hiển thị lỗi API ngay trên dưới form */}
        {apiError && <div className={styles.apiErrorMessage}>{apiError}</div>}
        <label>Username</label>

        <div className={styles.inputWrapper}>
          <FaRegUser className={styles.icon} />
          <input
            type="text"
            name="username" // Quan trọng : Thêm name
            placeholder="Enter username"
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
        <label>Password</label>
        <div className={styles.inputWrapper}>
          <FiLock className={styles.icon} />
          <input
            type={showPassword ? "text" : "password"}
            name="password" // Quan trọng : Thêm name
            placeholder="Enter password"
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
          <label htmlFor="remember">Remember me</label>
        </div>
        <Link to="/forgot-password" className={styles.forgotLink}>
          Forgot password?
        </Link>
      </div>
      <button type="submit" className={styles.submitButton}>
        Login
      </button>
    </form>
  );
};

export default LoginForm;
