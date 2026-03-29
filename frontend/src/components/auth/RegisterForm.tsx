//import { Link } from "react-router-dom";
import styles from "./Form.module.css";
import { FaRegUser } from "react-icons/fa";
import { FiLock, FiEye, FiEyeOff } from "react-icons/fi";
import { MdOutlineEmail } from "react-icons/md";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { registerUser } from "../../services/authService";
import { isAxiosError } from "axios";
import { useTranslation } from "react-i18next";

export type RegisterFormData = {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  gender: string;
  agree: boolean;
};

const validateField = (
  name: string,
  value: any,
  allValues: RegisterFormData,
  t: (key: string) => string
): string => {
  switch (name) {
    case "username":
      if (value.trim() === "") {
        return t("validation.error_username_required");
      }
      if (value.length < 3) {
        return t("validation.error_username_less_than_3");
      }
      if (value.length > 50) {
        return t("validation.error_username_more_than_50");
      }
      if (/[^a-zA-Z0-9_-]/.test(value)) {
        return t("validation.error_username_format");
      }
      return "";
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
    case "email":
      if (value.trim() === "") {
        return t("validation.error_email_required");
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        return t("validation.error_email_invalid");
      }
      return "";

    case "agree":
      if (!value) {
        // 'value' ở đây sẽ là 'true' hoặc 'false'
        return t("validation.error_terms_required");
      }
      return "";
    default:
      return "";
  }
};

const RegisterForm = () => {
  const { t } = useTranslation();

  // Tạo state cho tất cả dữ liệu form
  const [formData, setFormData] = useState<RegisterFormData>({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    gender: "male",
    agree: false,
  });

  // State cho các lỗi validation
  const [errors, setErrors] = useState({
    username: "",
    password: "",
    confirmPassword: "",
    email: "",
    agree: "",
  });

  // State cho lỗi từ API
  const [apiError, setApiError] = useState("");

  // State để quản lý hiển thị mật khẩu
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Khởi tạo hook
  const navigate = useNavigate();

  // Hàm xử lý khi người dùng nhập dữ liệu
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = event.target;

    // Cập nhật giá trị vào state
    const inputValue = type === "checkbox" ? checked : value;

    setFormData((prevData) => ({
      ...prevData,
      [name]: inputValue,
    }));

    // Xóa lỗi ngay khi người dùng bắt đầu nhập
    if (errors[name as keyof typeof errors]) {
      setErrors((prevErrors) => ({
        ...prevErrors,
        [name]: "",
      }));
    }

    // Xóa lỗi API khi người dùng bắt đầu nhập
    if (apiError) {
      setApiError("");
    }
  };

  // Hàm handleBlur (chạy khi người dùng rời khỏi input)
  const handleBlur = (event: React.FocusEvent<HTMLInputElement>) => {
    const { name, value } = event.target;

    // Cập nhật formData trước khi validate (vì state có thể chưa kịp upload)
    const currentFormData = { ...formData, [name]: value };
    const errorMessage = validateField(name, value, currentFormData, t);

    setErrors((prevErrors) => ({
      ...prevErrors,
      [name]: errorMessage,
    }));

    // Đặc biết : nếu sửa 'password' thì cũng cần validate lại 'confirmPassword'
    if (name === "password" && formData.confirmPassword) {
      const confirmPasswordError = validateField(
        "confirmPassword",
        formData.confirmPassword,
        currentFormData,
        t
      );
      setErrors((prevErrors) => ({
        ...prevErrors,
        confirmPassword: confirmPasswordError,
      }));
    }
  };

  // Hàm xử lý khi submit form
  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    // Validate tất cả các trường
    const usernameError = validateField(
      "username",
      formData.username,
      formData,
      t
    );
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
    const emailError = validateField("email", formData.email, formData, t);
    const agreeError = validateField("agree", formData.agree, formData, t);
    // let agreeError = "";
    // if (!formData.agree) {
    //   agreeError = "You must agree to the terms and conditions.";
    // }

    const allErrors = {
      username: usernameError,
      password: passwordError,
      confirmPassword: confirmPasswordError,
      email: emailError,
      agree: agreeError,
    };

    // Nếu có lỗi, cập nhật state lỗi và dừng submit
    if (Object.values(allErrors).some((error) => error !== "")) {
      setErrors(allErrors);
      return;
    }

    console.log("Form hợp lệ, đang gửi đăng ký:", formData);
    // Nếu không có lỗi, tiến hành submit form (gọi API)
    registerUser(formData)
      .then((response) => {
        // Đăng kí thành công
        console.log(response.data.message);
        // Chuyển hướng về trang đăng nhập
        navigate("/login");
      })
      .catch((error) => {
        // Xử lý lỗi từ API
        if (isAxiosError(error)) {
          if (
            error.response &&
            error.response.data &&
            error.response.data.message
          ) {
            // Lấy lỗi từ backend trả vè
            setApiError(error.response.data.message);
          } else {
            setApiError("Registration failed. Please try again.");
          }
        } else {
          // Nếu là lỗi khác (vd : lỗi mạng , lỗi code)
          console.error(error);
          setApiError("Một lỗi không xác định đã xảy ra.");
        }
      });
  };

  return (
    <form onSubmit={handleSubmit} noValidate>
      <title>{t("title.register_page")}</title>
      <div className={styles.formGroup}>
        <label>{t("auth_page.username")}</label>

        <div className={styles.inputWrapper}>
          <FaRegUser className={styles.icon} />
          <input
            type="text"
            name="username"
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
            name="password"
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
      <div className={styles.formGroup}>
        <label>{t("auth_page.confirm_password")}</label>
        <div className={styles.inputWrapper}>
          <FiLock className={styles.icon} />
          <input
            type={showConfirmPassword ? "text" : "password"}
            name="confirmPassword"
            placeholder={t("auth_page.confirm_password_placeholder")}
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
      <div className={styles.formGroup}>
        <label>{t("auth_page.email")}</label>
        <div className={styles.inputWrapper}>
          <MdOutlineEmail className={styles.icon} />
          <input
            type="email"
            name="email"
            placeholder="your.email@example.com"
            value={formData.email}
            onChange={handleChange}
            onBlur={handleBlur}
            className={errors.email ? styles.inputError : ""}
          />
        </div>
        {errors.email && <p className={styles.errorMessage}>{errors.email}</p>}
      </div>

      <div className={styles.optionsRow}>
        <div className={styles.radioGroup}>
          <input
            type="radio"
            id="male"
            name="gender"
            value="male"
            checked={formData.gender === "male"}
            onChange={handleChange}
          />
          <label htmlFor="male">{t("auth_page.male")}</label>
          <input
            type="radio"
            id="female"
            name="gender"
            value="female"
            checked={formData.gender === "female"}
            onChange={handleChange}
          />
          <label htmlFor="female">{t("auth_page.female")}</label>
        </div>
      </div>

      <div
        className={`${styles.agreeGroup} ${
          errors.agree ? styles.inputErrorGroup : ""
        }`}
      >
        <input
          type="checkbox"
          id="agree"
          name="agree"
          checked={formData.agree}
          onChange={handleChange}
        />

        <label htmlFor="agree">{t("auth_page.term")}</label>
      </div>
      {errors.agree && <p className={styles.errorMessage}>{errors.agree}</p>}
      <button type="submit" className={styles.submitButton}>
        {t("auth_page.register_button")}
      </button>
      {apiError && <div className={styles.apiErrorMessage}>{apiError}</div>}
    </form>
  );
};

export default RegisterForm;
