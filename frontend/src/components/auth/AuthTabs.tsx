import { useNavigate } from "react-router-dom";
import styles from "./AuthTabs.module.css";
import { useTranslation } from "react-i18next";

interface AuthTabsProps {
  active: "login" | "register";
}

const AuthTabs = ({ active }: AuthTabsProps) => {
  const navigate = useNavigate();

  const { t } = useTranslation();

  return (
    <div className={styles.tabs}>
      <button
        className={`${styles.tab} ${
          active === "login" ? styles.activeTab : ""
        }`}
        onClick={() => navigate("/login")}
      >
        {t("auth_page.login_tab")}
      </button>

      <button
        className={`${styles.tab} ${
          active === "register" ? styles.activeTab : ""
        }`}
        onClick={() => navigate("/register")}
      >
        {t("auth_page.register_tab")}
      </button>
    </div>
  );
};

export default AuthTabs;
