import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import SignupService from "../../services/SignupService";
import "@fortawesome/fontawesome-free/css/all.min.css";

const SignupForm = ({ switchForm }) => {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
  });
  const navigate = useNavigate();
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [confirmPasswordError, setConfirmPasswordError] = useState("");
  const [backendError, setBackendError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // --------------------------
  // VALIDATION FUNCTIONS
  // --------------------------
  const validateEmail = (value) => {
    if (!value || !value.trim()) return "Email is required";
    if (value.length > 254) return "Email is too long (max 254 characters)";
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!regex.test(value)) return "Invalid email format";
    return "";
  };

  const validatePassword = (value) => {
    // Nếu trống thì trả luôn lỗi "Password is required"
    if (!value || !value.trim()) return "Password is required";

    const errors = [];
    if (value.length < 8) errors.push("Password must be at least 8 characters");
    if (!/[A-Z]/.test(value))
      errors.push("Password must contain an uppercase letter");
    if (!/[a-z]/.test(value))
      errors.push("Password must contain a lowercase letter");
    if (!/[0-9]/.test(value)) errors.push("Password must contain a number");
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(value))
      errors.push("Password must contain a special character");

    // Logic hiển thị lỗi: 1 lỗi thì chi tiết, ≥2 lỗi thì lỗi chung
    if (errors.length === 0) return "";
    if (errors.length === 1) return errors[0];
    return "Password is invalid";
  };

  const validateConfirmPassword = (value) => {
    if (!value || !value.trim()) return "Confirm password is required";
    if (value !== formData.password) return "Passwords do not match";
    return "";
  };

  // --------------------------
  // HANDLERS
  // --------------------------
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });

    // realtime validation
    if (e.target.name === "email") setEmailError(validateEmail(e.target.value));
    if (e.target.name === "password")
      setPasswordError(validatePassword(e.target.value));
    if (e.target.name === "confirmPassword")
      setConfirmPasswordError(validateConfirmPassword(e.target.value));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBackendError("");

    // Validate all fields before submitting
    const emailErr = validateEmail(formData.email);
    const passwordErr = validatePassword(formData.password);
    const confirmErr = validateConfirmPassword(formData.confirmPassword);

    setEmailError(emailErr);
    setPasswordError(passwordErr);
    setConfirmPasswordError(confirmErr);

    if (emailErr || passwordErr || confirmErr) return;

    // --------------------------
    // SUBMIT TO BACKEND
    // --------------------------
    setIsSubmitting(true);
    try {
      const res = await SignupService.register(formData);
      setBackendError(res.message || "Sign up successful!");
    } catch (err) {
      console.error("Backend error:", err);
      try {
        const parsed = JSON.parse(err.message);
        setBackendError(parsed.message || "Sign up failed");
        console.log("Backend details:", parsed.details);
      } catch {
        setBackendError(err.message || "Sign up failed");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // --------------------------
  // JSX
  // --------------------------
  return (
    <div className="page-container">
      <div className="signup-box">
        <h2>Sign up</h2>
        <form onSubmit={handleSubmit} noValidate>
          {/* Email */}
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            onBlur={() => setEmailError(validateEmail(formData.email))}
          />
          {emailError && <p className="error-signup-message">{emailError}</p>}

          {/* Password */}
          <div className="input-wrapper">
            <input
              type={showPassword ? "text" : "password"}
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              onBlur={() =>
                setPasswordError(validatePassword(formData.password))
              }
            />
            <i
              className={`fa-solid ${showPassword ? "fa-eye" : "fa-eye-slash"}`}
              onClick={() => setShowPassword(!showPassword)}
              style={{ cursor: "pointer" }}
            ></i>
          </div>
          {passwordError && <p className="error-signup-message">{passwordError}</p>}

          {/* Confirm Password */}
          <div className="input-wrapper">
            <input
              type={showConfirmPassword ? "text" : "password"}
              name="confirmPassword"
              placeholder="Confirm Password"
              value={formData.confirmPassword}
              onChange={handleChange}
              onBlur={() =>
                setConfirmPasswordError(
                  validateConfirmPassword(formData.confirmPassword)
                )
              }
            />
            <i
              className={`fa-solid ${
                showConfirmPassword ? "fa-eye" : "fa-eye-slash"
              }`}
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              style={{ cursor: "pointer" }}
            ></i>
          </div>
          {confirmPasswordError && (
            <p className="error-signup-message">{confirmPasswordError}</p>
          )}

          <hr className="divider" />

          <button type="submit" disabled={isSubmitting}>
            Sign up
          </button>

          {backendError && <p className="error-signup-message">{backendError}</p>}
        </form>

        <p>
          Already have an account?{" "}
          <span
            onClick={() => navigate("/signin")}
            style={{ color: "#26b894", cursor: "pointer" }}
          >
            Sign in
          </span>
        </p>
      </div>
    </div>
  );
};

export default SignupForm;
