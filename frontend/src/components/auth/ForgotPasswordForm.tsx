// src/components/auth/ForgotPasswordForm.tsx

import { Link } from "react-router-dom";
import styles from "./Form.module.css"; // Dùng chung file CSS với các form khác
import { FaArrowLeft, FaInfoCircle } from "react-icons/fa";
import { MdOutlineEmail } from "react-icons/md";
import { useState } from "react";
import { requestPasswordReset } from "../../services/authService";
import { isAxiosError } from "axios";

const ForgotPasswordForm = () => {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [messageSent, setMessageSent] = useState(false);

  const handleSubmit = (event: React.FormEvent) => {
    event?.preventDefault();
    setError("");

    // Validate email đơn gian
    if (email.trim() === "" || !/\S+@\S+\.\S+/.test(email)) {
      setError("Vui lòng nhập địa chỉ email hợp lệ");
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
      <h2 className={styles.formTitle}>Forgot Your Password?</h2>
      <p className={styles.formSubtitle}>
        No worries! Enter your email address and we'll send you a link to reset
        your password.
      </p>

      {/* Email Input */}
      <div className={styles.formGroup}>
        <label htmlFor="email">Email Address</label>
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
        Send Reset Link
      </button>

      {/* Back to Login Link */}
      <div className={styles.backLinkWrapper}>
        <Link to="/login" className={styles.backLink}>
          <FaArrowLeft />
          <span>Back to Login</span>
        </Link>
      </div>

      {/* Tip Box */}
      <div className={styles.tipBox}>
        <FaInfoCircle className={styles.tipIcon} />
        <p>
          <strong>Tip:</strong> Make sure to use the email address associated
          with your account.
        </p>
      </div>
    </form>
  );
};

export default ForgotPasswordForm;
