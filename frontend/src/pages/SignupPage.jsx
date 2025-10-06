import React from "react";
import SignupForm from "../components/Signup/SignupForm";
import "../assets/styles/Signup.scss";

function SignupPage({ switchForm }) {
  return (
    <div className="page-container">
      <SignupForm switchForm={switchForm} />
    </div>
  );
}

export default SignupPage;
