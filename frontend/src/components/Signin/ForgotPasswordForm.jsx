import React, { useState } from "react";
import { Link } from "react-router-dom";
//import ForgotPasswordService from "../services/ForgotPasswordService";
import { FaArrowLeftLong } from "react-icons/fa6";

function ForgotPasswordForm() {
  //   const [email, setEmail] = useState("");
  //   const [message, setMessage] = useState("");
  //   const [loading, setLoading] = useState(false);

  //   const handleSubmit = async (e) => {
  //     e.preventDefault();
  //     setMessage("");
  //     setLoading(true);

  //     try {
  //       const response = await ForgotPasswordService.sendResetEmail(email);
  //       setMessage(response.message || "Reset link sent successfully!");
  //     } catch (error) {
  //       setMessage(error.message || "Failed to send reset link. Try again.");
  //     } finally {
  //       setLoading(false);
  //     }
  //   };

  //   return (
  //     <div className="forgot-page">
  //       {/* Form Box */}
  //       <div className="forgot-box">
  //         <div className="icon-lock">
  //           <i className="fa-solid fa-lock"></i>
  //         </div>
  //         <h2>Forgot your password?</h2>
  //         <p>
  //           No worries! Enter your email address and we’ll send you instructions
  //           to reset your password.
  //         </p>

  //         <form onSubmit={handleSubmit}>
  //           <label>Email address</label>
  //           <input
  //             type="email"
  //             placeholder=""
  //             value={email}
  //             onChange={(e) => setEmail(e.target.value)}
  //             required
  //           />
  //           <p>Enter the email address associated with your SkinAid account</p>
  //           <button type="submit" disabled={loading}>
  //             {loading ? "Sending..." : "Send Reset Instructions"}
  //           </button>
  //         </form>

  //         {message && <p className="message">{message}</p>}

  //         <Link to="/login" className="back-signin">
  //           ← Back to Sign in
  //         </Link>
  //       </div>

  //       {/* Footer */}
  //       <footer className="footer">© 2025 SkinAid. All rights reserved.</footer>
  //     </div>
  //   );
  return (
    <div className="forgot-page">
      {/* Form Box */}
      <div className="forgot-box">
        <div className="icon-lock">
          <i className="fa-solid fa-lock"></i>
        </div>

        <h2>Forgot your password?</h2>
        <p id="sub-title">
          No worries! Enter your email address and we’ll send you instructions
          to reset your password.
        </p>

        <form>
          <label>Email address</label>
          <input type="email" placeholder="you@example.com" required />
          <p id="form">
            Enter the email address associated with your SkinAid account
          </p>

          <button type="submit">Send Reset Instructions</button>
        </form>

        <div className="block-backsignin">
          <FaArrowLeftLong className="icon-back" />
          <Link to="/signin" className="back-signin">
            Back to Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}

export default ForgotPasswordForm;
