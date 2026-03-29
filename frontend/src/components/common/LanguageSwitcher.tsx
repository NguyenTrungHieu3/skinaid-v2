import { useTranslation } from "react-i18next";
import CountryFlag from "react-country-flag";
import styles from "./LanguageSwitcher.module.css"; // Style riêng cho component này

const LanguageSwitcher = () => {
  const { i18n } = useTranslation();

  return (
    <div className={styles.container}>
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
};

export default LanguageSwitcher;
