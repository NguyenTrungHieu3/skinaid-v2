import { useNavigate } from "react-router-dom";
import styles from "./AuthTabs.module.css";

interface AuthTabsProps {
  active: "login" | "register";
}

const AuthTabs = ({ active }: AuthTabsProps) => {
  const navigate = useNavigate();

  return (
    <div className={styles.tabs}>
      <button
        className={`${styles.tab} ${
          active === "login" ? styles.activeTab : ""
        }`}
        onClick={() => navigate("/login")}
      >
        LOGIN
      </button>

      <button
        className={`${styles.tab} ${
          active === "register" ? styles.activeTab : ""
        }`}
        onClick={() => navigate("/register")}
      >
        REGISTER
      </button>
    </div>
  );
};

export default AuthTabs;
