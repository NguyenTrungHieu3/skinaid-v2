// src/components/layout/Header.tsx
import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import styles from "./Header.module.css";
import Logo from "../../assets/images/general/logo.png";
import { useState } from "react";
import { FaBars } from "react-icons/fa";
import { useTranslation } from "react-i18next";
import CountryFlag from "react-country-flag";

const Header = () => {
  const { isAuthenticated, user, logout } = useAuth();

  // Thêm state để quản lí menu mobile
  const [menuOpen, setMenuOpen] = useState(false);

  const closeMenu = () => setMenuOpen(false);

  const { t, i18n } = useTranslation();
  // --- 2. TẠO COMPONENT CHUYỂN NGÔN NGỮ ---
  const LanguageSwitcher = () => (
    <div className={styles.languageSwitcher}>
      <button
        onClick={() => i18n.changeLanguage("en")}
        className={`${styles.flagButton} ${
          i18n.language === "en" ? styles.activeFlag : ""
        }`}
        aria-label="Switch to English"
      >
        <CountryFlag countryCode="US" svg />
      </button>
      <span className={styles.divider}>|</span>
      <button
        onClick={() => i18n.changeLanguage("vi")}
        className={`${styles.flagButton} ${
          i18n.language === "vi" ? styles.activeFlag : ""
        }`}
        aria-label="Switch to Vietnamese"
      >
        <CountryFlag countryCode="VN" svg />
      </button>
    </div>
  );
  return (
    <header className={styles.header}>
      {/* 1. NÚT HAMBURGER (BÊN TRÁI - CHỈ HIỆN TRÊN MOBILE) */}
      <button
        className={styles.hamburgerButton}
        onClick={() => setMenuOpen(!menuOpen)}
        aria-label="Toggle menu"
      >
        <FaBars />
      </button>

      {/* 2. LOGO (GIỮA TRÊN MOBILE - BÊN TRÁI TRÊN DESKTOP) */}
      <Link to="/" className={styles.logo} onClick={closeMenu}>
        <img src={Logo} alt="SkinAid Logo" />
        <span>
          Skin<span className={styles.logoAid}>Aid</span>
        </span>
      </Link>

      {/* 3. CONTAINER CHO MENU VÀ AUTH (MENU SLIDE TRÊN MOBILE - HIỆN RA TRÊN DESKTOP) */}
      <div
        className={`${styles.navContainer} ${
          menuOpen ? styles.mobileMenuOpen : ""
        }`}
      >
        {/* Lớp phủ (overlay) để bấm vào là tắt menu trên mobile */}
        {menuOpen && <div className={styles.overlay} onClick={closeMenu}></div>}

        {/* Nội dung menu (slide-in) */}
        <div className={styles.menuContent}>
          <nav className={styles.nav}>
            <NavLink
              to="/"
              onClick={closeMenu}
              className={({ isActive }) => (isActive ? styles.active : "")}
            >
              {t("header.home")}
            </NavLink>
            <NavLink
              to="/upload"
              onClick={closeMenu}
              className={({ isActive }) => (isActive ? styles.active : "")}
            >
              {t("header.upload_image")}
            </NavLink>

            {isAuthenticated && (
              <NavLink
                to="/history"
                onClick={closeMenu}
                className={({ isActive }) => (isActive ? styles.active : "")}
              >
                {t("header.wound_history")} {/* Giả sử bạn có key "history" */}
              </NavLink>
            )}

            <NavLink
              to="/about"
              onClick={closeMenu}
              className={({ isActive }) => (isActive ? styles.active : "")}
            >
              {t("header.about")}
            </NavLink>
          </nav>

          <div className={styles.rightWrapper}>
            <LanguageSwitcher />

            <div className={styles.authButtons}>
              {isAuthenticated ? (
                <>
                  <Link to="/profile" className={styles.welcomeLink}>
                    {t("header.hi")}, {user?.full_name || user?.user_name}
                  </Link>{" "}
                  <button
                    onClick={() => {
                      logout();
                      closeMenu();
                    }}
                    className={styles.authBtn}
                  >
                    {t("header.sign_out")}
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    onClick={closeMenu}
                    className={styles.authBtn}
                  >
                    {t("header.sign_in")}
                  </Link>
                  <Link
                    to="/register"
                    onClick={closeMenu}
                    className={`${styles.authBtn} ${styles.signUp}`}
                  >
                    {t("header.sign_up")}
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
