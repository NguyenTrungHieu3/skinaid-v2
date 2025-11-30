import { X, CheckCircle, AlertTriangle } from 'lucide-react';
import styles from './FirstAidManagement.module.css';

interface Guide {
    firstaidguide_id: string;
    wound_type: string;
    severity: string;
    severity_display?: string;
    sub_type?: string;
    title: string;
    description: string;
    steps: string[];
    supplies_needed: string[];
    dos: string[];
    donts: string[];
    estimated_healing_time?: string;
    source?: string;
    is_active: boolean;
    version: number;
    created_at: string;
    updated_at: string;
}

interface FirstAidViewModalProps {
    isOpen: boolean;
    guide: Guide | null;
    onClose: () => void;
    formatWoundType: (woundType: string) => string;
    getSeverityBadgeClass: (severity: string) => string;
}

/**
 * Modal component for viewing First Aid guide details
 * Extracted from FirstAidManagement for better code organization
 */
export default function FirstAidViewModal({
    isOpen,
    guide,
    onClose,
    formatWoundType,
    getSeverityBadgeClass
}: FirstAidViewModalProps) {
    if (!isOpen || !guide) return null;

    return (
        <div className={styles.modalOverlay}>
            <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
                <div className={styles.modalHeader}>
                    <h2>{guide.title}</h2>
                    <button className={styles.modalClose} onClick={onClose}>
                        <X size={24} />
                    </button>
                </div>

                <div className={styles.modalBody}>
                    <div className={styles.modalInfoGrid}>
                        <div className={styles.infoItem}>
                            <label>Wound Type</label>
                            <p>{formatWoundType(guide.wound_type)}</p>
                        </div>
                        <div className={styles.infoItem}>
                            <label>Severity</label>
                            <span className={`${styles.badge} ${getSeverityBadgeClass(guide.severity)}`}>
                                {guide.severity_display || guide.severity}
                            </span>
                        </div>
                        <div className={styles.infoItem}>
                            <label>Sub Type</label>
                            <p>{guide.sub_type || '-'}</p>
                        </div>
                        {guide.estimated_healing_time && (
                            <div className={styles.infoItem}>
                                <label>Healing Time</label>
                                <p>{guide.estimated_healing_time}</p>
                            </div>
                        )}
                    </div>

                    {guide.description && (
                        <div className={styles.modalSection}>
                            <h3>Description</h3>
                            <p>{guide.description}</p>
                        </div>
                    )}

                    {guide.steps && guide.steps.length > 0 && (
                        <div className={styles.modalSection}>
                            <h3>First Aid Steps</h3>
                            <ol className={styles.stepsListFull}>
                                {guide.steps.map((step, index) => (
                                    <li key={index}>
                                        <span className={styles.stepNumber}>{index + 1}</span>
                                        <span className={styles.stepText}>{step}</span>
                                    </li>
                                ))}
                            </ol>
                        </div>
                    )}

                    {guide.dos && guide.dos.length > 0 && (
                        <div className={`${styles.modalSection} ${styles.modalSectionSuccess}`}>
                            <h3>
                                <CheckCircle size={16} style={{ display: 'inline', marginRight: '8px' }} />
                                Do's
                            </h3>
                            <ul className={styles.tipsList}>
                                {guide.dos.map((item, index) => (
                                    <li key={index}>{item}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {guide.donts && guide.donts.length > 0 && (
                        <div className={`${styles.modalSection} ${styles.modalSectionDanger}`}>
                            <h3>
                                <AlertTriangle size={16} style={{ display: 'inline', marginRight: '8px' }} />
                                Don'ts
                            </h3>
                            <ul className={styles.tipsList}>
                                {guide.donts.map((item, index) => (
                                    <li key={index}>{item}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {guide.supplies_needed && guide.supplies_needed.length > 0 && (
                        <div className={styles.modalSection}>
                            <h3>Supplies Needed</h3>
                            <ul className={styles.suppliesList}>
                                {guide.supplies_needed.map((supply, index) => (
                                    <li key={index}>{supply}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <div className={styles.modalFooterInfo}>
                        <p><strong>Source:</strong> {guide.source || 'Based on WHO and Red Cross guidelines'}</p>
                        <p><strong>Version:</strong> {guide.version}</p>
                        <p><strong>Last Updated:</strong> {new Date(guide.updated_at).toLocaleDateString()}</p>
                    </div>
                </div>

                <div className={styles.modalActions}>
                    <button className={styles.btnSecondary} onClick={onClose}>
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}
