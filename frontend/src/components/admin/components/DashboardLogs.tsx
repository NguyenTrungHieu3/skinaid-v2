import { AlertCircle, CheckCircle, Info } from 'lucide-react';
import styles from './DashboardLogs.module.css';

interface Log {
  type: 'error' | 'success' | 'info';
  severity: 'high' | 'medium' | 'low';
  message: string;
  time: string;
}

interface DashboardLogsProps {
  logs: Log[];
}

export default function DashboardLogs({ logs }: DashboardLogsProps) {
  const getLogIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <AlertCircle className={styles.adminErrorLogsIcon} />;
      case 'success':
        return <CheckCircle className={styles.adminErrorLogsIcon} />;
      default:
        return <Info className={styles.adminErrorLogsIcon} />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    const labels = {
      high: 'High',
      medium: 'Medium',
      low: 'Low'
    };
    return labels[severity as keyof typeof labels] || severity;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return {
          bg: '#fef2f2',
          border: '#fecaca',
          icon: '#dc2626',
          badge: '#991b1b',
          badgeBg: '#fee2e2'
        };
      case 'medium':
        return {
          bg: '#fffbeb',
          border: '#fde68a',
          icon: '#d97706',
          badge: '#92400e',
          badgeBg: '#fef3c7'
        };
      default:
        return {
          bg: '#f0f9ff',
          border: '#bae6fd',
          icon: '#0284c7',
          badge: '#075985',
          badgeBg: '#e0f2fe'
        };
    }
  };

  return (
    <div className={`${styles.adminErrorLogs} ${styles.mt24}`}>
      <div className={styles.adminErrorLogsHeader}>
        <div>
          <h3 className={styles.adminErrorLogsTitle}>Recent Logs</h3>
          <p className={styles.adminErrorLogsDescription}>System notifications and alerts</p>
        </div>
      </div>
      <div className={styles.adminErrorLogsContent}>
        {logs.map((alert, index) => {
          const colors = getSeverityColor(alert.severity);
          return (
            <div
              className={styles.adminErrorLogsItem}
              key={index}
              style={{
                backgroundColor: colors.bg,
                borderColor: colors.border
              }}
            >
              <div style={{ color: colors.icon }}>
                {getLogIcon(alert.type)}
              </div>
              <div className={styles.adminErrorLogsInfo}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <p className={styles.adminErrorLogsInfoHeader}>{alert.message}</p>
                  <span style={{
                    fontSize: '0.75rem',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    backgroundColor: colors.badgeBg,
                    color: colors.badge,
                    fontWeight: '500'
                  }}>
                    {getSeverityBadge(alert.severity)}
                  </span>
                </div>
                <p className={styles.adminErrorLogsInfoDes}>{alert.time}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
