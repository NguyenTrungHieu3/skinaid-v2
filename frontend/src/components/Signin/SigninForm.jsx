import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import SigninService from "../../services/SigninService";
import "@fortawesome/fontawesome-free/css/all.min.css";

function SigninForm({ switchForm }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const navigate = useNavigate();

  // Validate Email
  const validateEmail = (value) => {
    if (!value || !value.trim()) return "Email is required";
    if (value.length > 254) return "Email is too long (maximum 254 characters)";
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) return "Invalid email format";
    return "";
  };

  // Validate Password
  const validatePassword = (value) => {
    const errors = [];
    if (!value || !value.trim()) {
      errors.push("Password is required");
      return errors;
    }
    if (value.length < 8) errors.push("Password must be at least 8 characters");
    if (!/[A-Z]/.test(value))
      errors.push("Password must contain at least one uppercase letter");
    if (!/[a-z]/.test(value))
      errors.push("Password must contain at least one lowercase letter");
    if (!/[0-9]/.test(value))
      errors.push("Password must contain at least one number");
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(value))
      errors.push("Password must contain at least one special character");
    return errors;
  };

  const handlePasswordValidation = (value) => {
    const errors = validatePassword(value);

    if (errors[0] === "Password is required") {
      setPasswordError(errors[0]);
      return;
    }

    if (errors.length === 1) {
      setPasswordError(errors[0]); // 1 lỗi: hiển thị chi tiết
    } else if (errors.length > 1) {
      setPasswordError("Password is invalid"); // 2 lỗi trở lên: hiển thị chung
    } else {
      setPasswordError(""); // hợp lệ
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage("");

    // FE Validation trước khi gọi BE
    const emailErr = validateEmail(email);
    const passwordErrs = validatePassword(password);

    setEmailError(emailErr);
    handlePasswordValidation(password);

    if (emailErr || passwordErrs.length > 0) return;

    try {
      const data = await SigninService.login(email, password);

      // Lưu token
      localStorage.setItem("token", data.token);
      if (data.refreshToken)
        localStorage.setItem("refreshToken", data.refreshToken);

      // Check if user has admin role and redirect accordingly
      if (data.user && data.user.roles && data.user.roles.includes("admin")) {
        navigate("/admin"); // Redirect admin users to admin dashboard
      } else {
        navigate("/"); // Redirect regular users to homepage
      }
    } catch (err) {
      console.error("Backend error:", err);

      // Lấy message từ BE nếu có
      if (err.response && err.response.data && err.response.data.message) {
        setErrorMessage(err.response.data.message);
      } else {
        setErrorMessage(err.message || "Login failed");
      }
    }
  };

  return (
    <form className="signin-box" onSubmit={handleSubmit} noValidate>
      <h2>Sign in</h2>

      {/* Email */}
      <div className="input-group">
        <i className="fa-solid fa-user icon"></i>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (validateEmail(e.target.value) === "") setEmailError("");
          }}
          onBlur={() => setEmailError(validateEmail(email))}
          required
        />
      </div>
      {emailError && <p className="error-signin-message">{emailError}</p>}

      {/* Password */}
      <div className="input-group">
        <i className="fa-solid fa-lock icon"></i>
        <input
          type={showPassword ? "text" : "password"}
          placeholder="Password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            handlePasswordValidation(e.target.value);
          }}
          onBlur={() => handlePasswordValidation(password)}
          required
        />
        <i
          className={`fa-solid toggle-password ${
            showPassword ? "fa-eye" : "fa-eye-slash"
          }`}
          onClick={() => setShowPassword(!showPassword)}
        ></i>
      </div>
      {passwordError && <p className="error-signin-message">{passwordError}</p>}

      {/* Options */}
      <div className="options">
        <label>
          <input type="checkbox" /> Remember me
        </label>
        <a href="/" className="forgot-link">
          Forgot password?
        </a>
      </div>

      <hr className="divider" />

      {/* Buttons */}
      <div className="button-group">
        <button type="submit" className="btn btn-primary">
          Sign in
        </button>
        <button
          type="button"
          className="btn btn-outline"
          onClick={() => navigate("/signup")}
        >
          Sign up
        </button>
      </div>

      {/* Backend/general error */}
      {errorMessage && <p className="error-message">{errorMessage}</p>}
    </form>
  );
}

export default SigninForm;
