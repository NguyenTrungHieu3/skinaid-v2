import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "../../assets/styles/components/header.scss";
import LogoHome from "../../assets/images/logo.png";
import { FaBars, FaTimes } from "react-icons/fa";

export default function Header() {
  const location = useLocation();
  const isForgotPage = location.pathname === "/forgot-pass";
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="header">
      <div className="logo">
        <Link to="/" className="logo-link">
          <img src={LogoHome} alt="logo" />
          Skin<span>Aid</span>
        </Link>
      </div>

      {!isForgotPage && (
        <>
          <div className="hamburger" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <FaTimes /> : <FaBars />}
          </div>

          <div className={`menu ${menuOpen ? "show" : ""}`}>
            <nav>
              <Link to="/" className="home">
                Home
              </Link>
              <Link to="/upload" className="upload-img">
                Upload Image
              </Link>
              <Link to="/results" className="about">
                About
              </Link>
            </nav>
            <div className="auth">
              <Link to="/signin" className="signin">
                Sign in
              </Link>
              <Link to="/signup" className="signup">
                Sign up
              </Link>
            </div>
          </div>
        </>
      )}
    </header>
  );
}
