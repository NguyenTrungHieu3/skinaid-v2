import React from "react";
import "../assets/styles/Signin.scss";
import SigninForm from "../components/Signin/SigninForm";

function SigninPage() {
  const switchForm = () => {
    alert("Chuyển sang trang Sign up");
  };

  return (
    <div className="signin-container">
      <SigninForm switchForm={switchForm} />
    </div>
  );
}

export default SigninPage;
