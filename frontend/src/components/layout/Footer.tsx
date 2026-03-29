// src/components/layout/Footer.tsx
import styles from "./Footer.module.css";
import { Link } from "react-router-dom";
import FooterLogo from "../../assets/images/general/logo.png";
import { useTranslation } from "react-i18next";

const Footer = () => {
  const { t } = useTranslation();

  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <div className={styles.column}>
          <Link to="/" className={styles.logo}>
            <img
              src={FooterLogo}
              alt="SkinAid logo"
              className={styles.footerLogoImg}
            />
            <span>SkinAid</span>
          </Link>
          <p>{t("footer.title_desc")}</p>
        </div>
        <div className={styles.column}>
          <h4>{t("footer.column_1")}</h4>
          <Link to="/upload">{t("footer.column_1_uploadIMG")}</Link>
          <Link to="/history">{t("footer.column_1_history")}</Link>
          <Link to="/security">{t("footer.column_1_security")}</Link>
        </div>
        <div className={styles.column}>
          <h4>{t("footer.column_2")}</h4>
          <Link to="/contact">{t("footer.column_2_contact")}</Link>
          <Link to="/support-center">
            {t("footer.column_2_support_center")}
          </Link>
          <Link to="/api-docs">{t("footer.column_2_api")}</Link>
        </div>
        <div className={styles.column}>
          <h4>{t("footer.column_3")}</h4>
          <Link to="/about">{t("footer.column_3_about")}</Link>
          <Link to="/careers">{t("footer.column_3_careers")}</Link>
          <Link to="/privacy">{t("footer.column_3_privacy")}</Link>
        </div>
      </div>
      <div className={styles.bottomBar}>{t("footer.bottom_bar")}</div>
    </footer>
  );
};
export default Footer;
