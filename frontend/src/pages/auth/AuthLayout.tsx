import React from "react";
import styles from "./Auth.module.css";
import authImage from "../../assets/images/auths/anhNen2.jpg";
import Logo from "../../assets/images/general/logo.png"; // <-- Bạn cần thay bằng ảnh của mình
import { Link } from "react-router-dom";

// 1. Thêm prop 'align' vào
interface AuthLayoutProps {
  children: React.ReactNode;
  align?: "top" | "center"; // 'top' là mặc định, 'center' là để căn giữa
}

// Component này nhận vào một component con (children) để hiển thị form bên phải
const AuthLayout = ({ children, align = "top" }: AuthLayoutProps) => {
  return (
    <div className={styles.container}>
      <div className={styles.card}>
        {/* Left Decorative Panel */}
        <div className={styles.leftPanel}>
          <Link to="/" className={styles.leftPanelLogo}>
            <img src={Logo} alt="Logo Error" />
            <h2>SkinAid</h2>
          </Link>
          <img
            src={authImage}
            alt="Healthcare illustration"
            className={styles.promoImage}
          />
          <h1 className={styles.promoTitle}>Welcome to SkinAid</h1>
          <p className={styles.promoText}>
            Smart Wound Detection & Classification System
          </p>
        </div>

        {/* Right Form Panel */}
        {/* <div className={styles.rightPanel}>{children}</div> */}
        <div
          className={`
            ${styles.rightPanel} 
            ${align === "center" ? styles.alignCenter : styles.alignTop}
          `}
        >
          {children}
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
