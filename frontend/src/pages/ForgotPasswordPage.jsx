import React, { useEffect } from "react";
import "../assets/styles/ForgotPass.scss";
import ForgotPasswordForm from "../components/Signin/ForgotPasswordForm";
import Header from "../components/HomePage/Header";

function ForgotPasswordPage() {
  const switchForm = () => {
    alert("Chuyển sang trang Sign up");
  };

  useEffect(() => {
    document.title = "Forgot password | SkinAid";
  }, []);

  return (
    <div className="forgot-password-container">
      <Header />
      <ForgotPasswordForm switchForm={switchForm} />
    </div>
  );
}

export default ForgotPasswordPage;
