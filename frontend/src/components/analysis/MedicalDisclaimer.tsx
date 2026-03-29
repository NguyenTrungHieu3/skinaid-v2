import styles from "./MedicalDisclaimer.module.css";
import { FaExclamationCircle } from "react-icons/fa";
import { useTranslation } from "react-i18next";

const MedicalDisclaimer = () => {
  const { t } = useTranslation();

  return (
    <div className={styles.disclaimer}>
      <FaExclamationCircle className={styles.disclaimerIcon} />
      <div className={styles.disclaimerText}>
        <strong>{t("analysis.medical_title")}</strong>
        <p>{t("analysis.medical_desc")}</p>
      </div>
    </div>
  );
};

export default MedicalDisclaimer;
