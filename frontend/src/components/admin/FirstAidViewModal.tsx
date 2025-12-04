import { X, CheckCircle, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
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
    source?: {
        name: string;
        url?: string;
    } | string;
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
    const { t } = useTranslation();
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
                            <label>{t('admin.first_aid_view.labels.wound_type')}</label>
                            <p>{t(`admin.first_aid_form.options.${guide.wound_type}`) || formatWoundType(guide.wound_type)}</p>
                        </div>
                        <div className={styles.infoItem}>
                            <label>{t('admin.first_aid_view.labels.severity')}</label>
                            <span className={`${styles.badge} ${getSeverityBadgeClass(guide.severity)}`}>
                                {t(`admin.first_aid_form.options.${guide.severity}`) || guide.severity_display || guide.severity}
                            </span>
                        </div>
                        <div className={styles.infoItem}>
                            <label>{t('admin.first_aid_view.labels.sub_type')}</label>
                            <p>{guide.sub_type || '-'}</p>
                        </div>
                        {guide.estimated_healing_time && (
                            <div className={styles.infoItem}>
                                <label>{t('admin.first_aid_view.labels.healing_time')}</label>
                                <p>{guide.estimated_healing_time}</p>
                            </div>
                        )}
                        {guide.source && (
                            <div className={styles.infoItem}>
                                <label>{t('admin.first_aid_view.labels.source')}</label>
                                <p>
                                    {typeof guide.source === 'string' ? (
                                        guide.source
                                    ) : (
                                        <>
                                            <span style={{ fontWeight: 500 }}>{guide.source.name}</span>
                                            {guide.source.url && (
                                                <>
                                                    {' - '}
                                                    <a
                                                        href={guide.source.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        style={{ color: '#2563eb', textDecoration: 'underline' }}
                                                    >
                                                        {guide.source.url}
                                                    </a>
                                                </>
                                            )}
                                        </>
                                    )}
                                </p>
                            </div>
                        )}
                    </div>

                    {guide.description && (
                        <div className={styles.modalSection}>
                            <h3>{t('admin.first_aid_view.labels.description')}</h3>
                            <p>{guide.description}</p>
                        </div>
                    )}

                    {guide.steps && guide.steps.length > 0 && (
                        <div className={styles.modalSection}>
                            <h3>{t('admin.first_aid_view.labels.steps')}</h3>
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
                                {t('admin.first_aid_view.labels.dos')}
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
                                {t('admin.first_aid_view.labels.donts')}
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
                            <h3>{t('admin.first_aid_view.labels.supplies')}</h3>
                            <ul className={styles.suppliesList}>
                                {guide.supplies_needed.map((supply, index) => (
                                    <li key={index}>{supply}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <div className={styles.modalFooterInfo}>
                        <p><strong>{t('admin.first_aid_view.labels.version')}:</strong> {guide.version}</p>
                        <p><strong>{t('admin.first_aid_view.labels.last_updated')}:</strong> {new Date(guide.updated_at).toLocaleDateString()}</p>
                    </div>
                </div>

                <div className={styles.modalActions}>
                    <button className={styles.btnSecondary} onClick={onClose}>
                        {t('admin.first_aid_view.close')}
                    </button>
                </div>
            </div>
        </div>
    );
}
