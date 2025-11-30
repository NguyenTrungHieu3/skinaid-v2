// src/components/auth/ForgotPasswordForm.tsx

import { Link } from "react-router-dom";
import styles from "./Form.module.css"; // Dùng chung file CSS với các form khác
import { FaArrowLeft, FaInfoCircle } from "react-icons/fa";
import { MdOutlineEmail } from "react-icons/md";
import { useState } from "react";
import { requestPasswordReset } from "../../services/authService";
import { isAxiosError } from "axios";
import { useTranslation } from "react-i18next";

const ForgotPasswordForm = () => {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [messageSent, setMessageSent] = useState(false);

  const { t } = useTranslation();

  const handleSubmit = (event: React.FormEvent) => {
    event?.preventDefault();
    setError("");

    // Validate email đơn gian
    if (email.trim() === "" || !/\S+@\S+\.\S+/.test(email)) {
      setError(t("error_email_invalid"));
      return;
    }

    // GỌI API
    requestPasswordReset(email)
      .then(() => {
        // Bất kể API nói gì , chúng ta chỉ hiện thị thông báo thành công
        setMessageSent(true);
      })
      .catch((err) => {
        // Xử lí lỗi nếu có
        if (isAxiosError(err)) {
          setError(err.response?.data?.message || "Lỗi: Không thể gửi mail.");
        } else {
          setError("Đã có lỗi xảy ra. Vui lòng gửi lại.");
        }
      });
  };

  if (messageSent) {
    return (
      <div className={styles.form}>
        <h2 className={styles.formTitle}>Kiểm tra Email của bạn</h2>
        <p className={styles.formSubtitle}>
          Một link để reset mật khẩu đã được gửi đến <strong>{email}</strong>{" "}
          (nếu tài khoản tồn tại).
        </p>
        <div className={styles.backLinkWrapper}>
          <Link to="/login" className={styles.backLink}>
            <FaArrowLeft />
            <span>Back to Login</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <title>{t("title.forgot_password_page")}</title>
      <h2 className={styles.formTitle}>
        {t("auth_page.forgot_password_title")}
      </h2>
      <p className={styles.formSubtitle}>
        {t("auth_page.forgot_password_subtitle")}
      </p>

      {/* Email Input */}
      <div className={styles.formGroup}>
        <label htmlFor="email">{t("auth_page.forgot_password_email")}</label>
        <div className={styles.inputWrapper}>
          <MdOutlineEmail className={styles.icon} />
          <input
            type="email"
            id="email"
            name="email"
            placeholder="your.email@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={error ? styles.inputError : ""}
          />
        </div>
        {error && <p className={styles.errorMessage}>{error}</p>}
      </div>

      {/* Submit Button */}
      <button type="submit" className={styles.submitButton}>
        {t("auth_page.forgot_password_button")}
      </button>

      {/* Back to Login Link */}
      <div className={styles.backLinkWrapper}>
        <Link to="/login" className={styles.backLink}>
          <FaArrowLeft />
          <span>{t("auth_page.forgot_password_back_to_login")}</span>
        </Link>
      </div>

      {/* Tip Box */}
      <div className={styles.tipBox}>
        <FaInfoCircle className={styles.tipIcon} />
        <p>
          <strong>{t("auth_page.forgot_password_tip")}</strong>
          {t("auth_page.forgot_password_tip_desc")}
        </p>
      </div>
    </form>
  );
};

export default ForgotPasswordForm;
