import React from "react";
import styles from "./Auth.module.css";
import authImage from "../../assets/images/auths/anhNen2.jpg";
import Logo from "../../assets/images/general/logo.png"; // <-- Bạn cần thay bằng ảnh của mình
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import LanguageSwitcher from "../../components/common/LanguageSwitcher"; // <--- IMPORT Ở ĐÂY
import { FaArrowLeft } from "react-icons/fa"; // <--- 1. IMPORT ICON

// 1. Thêm prop 'align' vào
interface AuthLayoutProps {
  children: React.ReactNode;
  align?: "top" | "center"; // 'top' là mặc định, 'center' là để căn giữa
}

// Component này nhận vào một component con (children) để hiển thị form bên phải
const AuthLayout = ({ children, align = "top" }: AuthLayoutProps) => {
  const { t } = useTranslation();

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
          <h1 className={styles.promoTitle}>{t("auth_page.left_title")}</h1>
          <p className={styles.promoText}>{t("auth_page.left_desc")}</p>
        </div>

        {/* Right Form Panel */}
        {/* <div className={styles.rightPanel}>{children}</div> */}
        <div
          className={`
            ${styles.rightPanel} 
            ${align === "center" ? styles.alignCenter : styles.alignTop}
          `}
        >
          {/* --- 2. THÊM NÚT QUAY LẠI Ở ĐÂY --- */}
          <Link to="/" className={styles.mobileBackButton}>
            <FaArrowLeft />
          </Link>

          <div className={styles.languageWrapper}>
            <LanguageSwitcher />
          </div>
          {children}
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
