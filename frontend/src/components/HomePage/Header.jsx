import React from "react";
import { Link } from "react-router-dom";
import "../../assets/styles/components/header.scss";
import LogoHome from "../../assets/images/logo.png";

export default function Header() {
  return (
    <header className="header">
      <div className="logo">
        <img src={LogoHome} alt="logo" />
        Skin<span>Aid</span>
      </div>
      <nav>
        <Link to="/" className="home">
          Home
        </Link>
        <Link to="/upload" className="upload-img">
          Upload Image
        </Link>
        <a href="#about">About</a>
      </nav>
      <div className="auth">
        <Link to="/signin" className="signin">
          Sign in
        </Link>
        <Link to="/signup" className="signup">
          Sign up
        </Link>
      </div>
    </header>
  );
}
