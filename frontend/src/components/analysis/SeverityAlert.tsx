import { useTranslation } from "react-i18next";
import { FaExclamationTriangle, FaMapMarkerAlt } from "react-icons/fa";
import styles from "./SeverityAlert.module.css";

interface SeverityAlertProps {
  severity: string;
  onFindFacility: () => void;
}

/**
 * Alert component that displays when wound severity is moderate or severe.
 * Prompts user to find nearby medical facilities.
 */
const SeverityAlert = ({ severity, onFindFacility }: SeverityAlertProps) => {
  const { t } = useTranslation();

  // Determine alert level for styling
  const isSevere = severity.toLowerCase() === "severe";
  const alertClass = isSevere ? styles.severe : styles.moderate;

  return (
    <div className={`${styles.alertContainer} ${alertClass}`}>
      <div className={styles.alertContent}>
        <div className={styles.iconWrapper}>
          <FaExclamationTriangle className={styles.warningIcon} />
        </div>
        <div className={styles.textContent}>
          <h3 className={styles.alertTitle}>
            {t("severity_alert.title")}
          </h3>
          <p className={styles.alertDescription}>
            {isSevere
              ? t("severity_alert.severe_message")
              : t("severity_alert.moderate_message")}
          </p>
        </div>
      </div>
      <button className={styles.findButton} onClick={onFindFacility}>
        <FaMapMarkerAlt className={styles.buttonIcon} />
        <span>{t("severity_alert.find_facility")}</span>
      </button>
    </div>
  );
};

export default SeverityAlert;
