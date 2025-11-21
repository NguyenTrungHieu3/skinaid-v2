import styles from './MedicalDisclaimer.module.css';
import { FaExclamationCircle } from 'react-icons/fa';

const MedicalDisclaimer = () => {
  return (
    <div className={styles.disclaimer}>
      <FaExclamationCircle className={styles.disclaimerIcon} />
      <div className={styles.disclaimerText}>
        <strong>Important Medical Disclaimer</strong>
        <p>
          This AI analysis is for informational purposes only and should not replace 
          professional medical advice. Always consult with a healthcare provider 
          for proper wound assessment and treatment.
        </p>
      </div>
    </div>
  );
};

export default MedicalDisclaimer;