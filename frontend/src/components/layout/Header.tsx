import { Link, NavLink, useLocation } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import styles from "./Header.module.css";
import Logo from "../../assets/images/general/logo.png";
import { FaBars, FaChevronDown } from "react-icons/fa";
import { useTranslation } from "react-i18next";
import CountryFlag from "react-country-flag";
import LanguageSwitcher from "../common/LanguageSwitcher";

interface HeaderProps {
  menuOpen: boolean;
  setMenuOpen: (open: boolean) => void;
}

const Header = ({ menuOpen, setMenuOpen }: HeaderProps) => {
  const [mobileSubmenuOpen, setMobileSubmenuOpen] = useState(false);
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();
  const isMapPage = location.pathname === "/map";

  const closeMenu = () => {
    setMenuOpen(false);
  };

  const { t } = useTranslation();

  return (
    <header className={`${styles.header} ${isMapPage ? styles.mapHeader : ""}`}>
      {/* 1. NÚT HAMBURGER (BÊN TRÁI - CHỈ HIỆN TRÊN MOBILE) */}
      <button
        className={styles.hamburgerButton}
        onClick={() => setMenuOpen(!menuOpen)}
        aria-label="Toggle menu"
      >
        <FaBars />
      </button>

      {/* 2. LOGO (GIỮA TRÊN MOBILE - BÊN TRÁI TRÊN DESKTOP) */}
      <Link
        to="/"
        className={styles.logo}
        onClick={() => {
          window.scrollTo({ top: 0, behavior: "smooth" });
          closeMenu();
        }}
      >
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
              onClick={() => {
                window.scrollTo({ top: 0, behavior: "smooth" });
                closeMenu();
              }}
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

            <NavLink
              to="/map"
              onClick={closeMenu}
              className={({ isActive }) => (isActive ? styles.active : "")}
            >
              {t("header.map")}
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

            {/* Dropdown for Sections */}
            <div
              className={`${styles.dropdown} ${
                mobileSubmenuOpen ? styles.mobileSubmenuOpen : ""
              }`}
            >
              <button
                className={styles.dropdownBtn}
                onClick={() => setMobileSubmenuOpen(!mobileSubmenuOpen)}
              >
                {t("header.explore")}
                <FaChevronDown className={styles.chevron} />
              </button>
              <div className={styles.dropdownContent}>
                <a href="/#how-it-works" onClick={closeMenu}>
                  {t("header.how_it_works")}
                </a>
                <a href="/#why-skinaid" onClick={closeMenu}>
                  {t("header.why_skinaid")}
                </a>
                <a href="/#features" onClick={closeMenu}>
                  {t("header.features")}
                </a>
                <a href="/#trust-safety" onClick={closeMenu}>
                  {t("header.trust_safety")}
                </a>
                <a href="/#medical-disclaimer" onClick={closeMenu}>
                  {t("header.medical_disclaimer")}
                </a>
              </div>
            </div>

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
