import React, { useState, useEffect } from "react";
import { FaCheckCircle, FaTimesCircle, FaSpinner } from "react-icons/fa";
import { useNavigate, useSearchParams } from "react-router-dom";
import VerifyService from "../../services/VerifyService";
import "../../assets/styles/Verify.scss";

const VerifyForm = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [verificationState, setVerificationState] = useState("loading");
  const [message, setMessage] = useState("");
  const [debugInfo, setDebugInfo] = useState("");

  useEffect(() => {
    const verifyEmailFromUrl = async () => {
      const email = searchParams.get("email");
      const token = searchParams.get("token");

      console.log("📧 Email verification started");
      console.log("Email:", email);
      console.log("Token:", token ? token.substring(0, 20) + "..." : "None");

      if (!email || !token) {
        console.error("❌ Missing email or token in URL");
        setVerificationState("error");
        setMessage("Invalid verification link. Missing email or token.");
        setDebugInfo(`Email: ${email || 'missing'}, Token: ${token ? 'present' : 'missing'}`);
        return;
      }

      try {
        setVerificationState("loading");
        setMessage("Verifying your email address...");
        
        const response = await VerifyService.verifyEmail(email, token);
        
        console.log("✅ Verification successful:", response);
        setVerificationState("success");
        setMessage(response.data?.message || "Email verified successfully!");
        setDebugInfo(`Verification completed for ${email}`);
        
      } catch (error) {
        console.error("❌ Verification failed:", error);
        setVerificationState("error");
        setMessage(error.message || "Email verification failed. Please try again.");
        setDebugInfo(`Error: ${error.code || 'UNKNOWN'} - ${error.message}`);
      }
    };

    verifyEmailFromUrl();
  }, [searchParams]);

  const renderContent = () => {
    switch (verificationState) {
      case "loading":
        return (
          <>
            <div className="verify-icon">
              <FaSpinner size={48} color="#3b82f6" className="spinning" />
            </div>
            <h2>Verifying your email...</h2>
            <p>Please wait while we verify your email address.</p>
          </>
        );

      case "success":
        return (
          <>
            <div className="verify-icon">
              <FaCheckCircle size={48} color="#22c55e" />
            </div>
            <h2>Email verification successful!</h2>
            <p>{message}</p>
            <p>Your account has been activated successfully.</p>
            <button 
              className="btn btn-primary" 
              onClick={() => navigate("/signin")}
            >
              Sign in now
            </button>
          </>
        );

      case "error":
        return (
          <>
            <div className="verify-icon">
              <FaTimesCircle size={48} color="#ef4444" />
            </div>
            <h2>Email verification failed</h2>
            <p>{message}</p>
            <div className="error-actions">
              <button 
                className="btn btn-primary" 
                onClick={() => navigate("/signin")}
              >
                Try signing in
              </button>
              <button 
                className="btn btn-outline" 
                onClick={() => navigate("/signup")}
              >
                Sign up again
              </button>
            </div>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <div className="verify-container">
      <div className="verify-card">
        {renderContent()}
        
        {debugInfo && (
          <div className="debug-info">
            <small>{debugInfo}</small>
          </div>
        )}
        
        <p className="support-text">
          If you have any questions, please{" "}
          <a href="/support">contact support</a>
        </p>
      </div>

      <footer className="verify-footer">
        © 2025 SkinAid. All rights reserved.
      </footer>
    </div>
  );
};

export default VerifyForm;
