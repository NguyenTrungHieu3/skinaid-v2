import { X, Clock, User, Shield, Activity, FileText, AlertTriangle, CheckCircle, Info, AlertCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import styles from './LogDetailsModal.module.css';

interface Log {
    id: string;
    action: string;
    user: string;
    email?: string;
    role: string;
    timestamp: string;
    details: string;
    type: 'error' | 'warning' | 'info' | 'success';
    severity: 'high' | 'medium' | 'low';
    ip: string;
    fullDetails?: any; // For the raw JSON details
}

interface LogDetailsModalProps {
    log: Log;
    onClose: () => void;
}

const LogDetailsModal: React.FC<LogDetailsModalProps> = ({ log, onClose }) => {
    const { t } = useTranslation();
    // Prevent click propagation to close modal when clicking inside content
    const handleContentClick = (e: React.MouseEvent) => {
        e.stopPropagation();
    };

    const getLogTypeIcon = (type: string) => {
        switch (type) {
            case 'error': return <AlertCircle size={20} className={styles.iconError} />;
            case 'warning': return <AlertTriangle size={20} className={styles.iconWarning} />;
            case 'success': return <CheckCircle size={20} className={styles.iconSuccess} />;
            default: return <Info size={20} className={styles.iconInfo} />;
        }
    };

    const getSeverityClass = (severity: string) => {
        switch (severity) {
            case 'high': return styles.severityHigh;
            case 'medium': return styles.severityMedium;
            default: return styles.severityLow;
        }
    };

    // Format JSON for display
    const formattedDetails = log.fullDetails
        ? JSON.stringify(log.fullDetails, null, 2)
        : log.details;

    return (
        <div className={styles.modalOverlay}>
            <div className={styles.modalContent} onClick={handleContentClick}>
                <div className={styles.modalHeader}>
                    <div className={styles.headerTitle}>
                        {getLogTypeIcon(log.type)}
                        <h2>{t('admin.logs.details.title')}</h2>
                    </div>
                    <button className={styles.closeButton} onClick={onClose}>
                        <X size={24} />
                    </button>
                </div>

                <div className={styles.modalBody}>
                    {/* Summary Section */}
                    <div className={styles.section}>
                        <h3 className={styles.sectionTitle}>{t('admin.logs.details.summary')}</h3>
                        <div className={styles.grid}>
                            <div className={styles.infoItem}>
                                <Clock size={16} />
                                <span className={styles.label}>{t('admin.logs.details.timestamp')}</span>
                                <span className={styles.value}>
                                    {new Date(log.timestamp).toLocaleString('en-US', {
                                        year: 'numeric',
                                        month: '2-digit',
                                        day: '2-digit',
                                        hour: '2-digit',
                                        minute: '2-digit',
                                        second: '2-digit',
                                        hour12: true
                                    })}
                                </span>
                            </div>
                            <div className={styles.infoItem}>
                                <Activity size={16} />
                                <span className={styles.label}>{t('admin.logs.details.action')}</span>
                                <span className={styles.value}>{log.action}</span>
                            </div>
                            <div className={styles.infoItem}>
                                <Shield size={16} />
                                <span className={styles.label}>{t('admin.logs.details.severity')}</span>
                                <span className={`${styles.badge} ${getSeverityClass(log.severity)}`}>
                                    {log.severity.toUpperCase()}
                                </span>
                            </div>
                            <div className={styles.infoItem}>
                                <User size={16} />
                                <span className={styles.label}>{t('admin.logs.details.user')}</span>
                                <span className={styles.value}>
                                    {log.user}
                                    {log.email && <span style={{ fontSize: '0.8em', color: '#64748b', marginLeft: '4px' }}>({log.email})</span>}
                                </span>
                            </div>

                        </div>
                    </div>

                    {/* Details Section */}
                    <div className={styles.section}>
                        <h3 className={styles.sectionTitle}>
                            <FileText size={18} />
                            {t('admin.logs.details.full_details')}
                        </h3>
                        <div className={styles.codeBlock}>
                            <pre>{formattedDetails}</pre>
                        </div>
                    </div>
                </div>

                <div className={styles.modalFooter}>
                    <button className={styles.closeBtn} onClick={onClose}>
                        {t('admin.logs.details.close')}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default LogDetailsModal;
