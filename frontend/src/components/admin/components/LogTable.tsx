import React from 'react';
import {
  AlertCircle,
  CheckCircle,
  Info,
  AlertTriangle,
  Loader
} from 'lucide-react';
import Pagination from '../../common/Pagination';
import styles from './LogTable.module.css';

interface Log {
  id: string;
  action: string;
  user: string;
  role: string;
  timestamp: string;
  details: string;
  type: 'error' | 'warning' | 'info' | 'success';
  severity: 'high' | 'medium' | 'low';
  ip: string;
}

interface PaginationData {
  currentPage: number;
  totalPages: number;
  totalLogs: number;
  limit: number;
}

interface LogTableProps {
  logs: Log[];
  isLoading: boolean;
  error: string | null;
  pagination: PaginationData;
  onPageChange: (page: number) => void;
}

const LogTable: React.FC<LogTableProps> = ({
  logs,
  isLoading,
  error,
  pagination,
  onPageChange
}) => {
  const getLogTypeIcon = (type: string) => {
    switch (type) {
      case 'error': return <AlertCircle size={16} />;
      case 'warning': return <AlertTriangle size={16} />;
      case 'success': return <CheckCircle size={16} />;
      default: return <Info size={16} />;
    }
  };

  const getLogTypeClass = (type: string) => {
    switch (type) {
      case 'error': return styles.logBadgeError;
      case 'warning': return styles.logBadgeWarning;
      case 'success': return styles.logBadgeSuccess;
      default: return styles.logBadgeInfo;
    }
  };

  const getSeverityClass = (severity: string) => {
    switch (severity) {
      case 'high': return styles.severityBadgeHigh;
      case 'medium': return styles.severityBadgeMedium;
      default: return styles.severityBadgeLow;
    }
  };

  if (isLoading) {
    return (
      <div className={styles.logsTableCard}>
        <div className={styles.loadingState}>
          <Loader className={styles.spinner} />
          <p>Loading logs...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.logsTableCard}>
        <div className={styles.errorState}>
          <AlertCircle size={48} />
          <p>{error}</p>
          <button
            className={styles.paginationBtn}
            onClick={() => window.location.reload()}
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!logs.length) {
    return (
      <div className={styles.logsTableCard}>
        <div className={styles.emptyState}>
          <Info size={48} />
          <p>No logs found matching your criteria</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.logsTableCard}>
      <div className={styles.cardHeader}>
        <h3>System Activity</h3>
        <span className={styles.pageInfo}>
          Showing {((pagination.currentPage - 1) * pagination.limit) + 1}-
          {Math.min(pagination.currentPage * pagination.limit, pagination.totalLogs)} of {pagination.totalLogs}
        </span>
      </div>

      <div className={styles.cardContent}>
        <div className={styles.logsTableWrapper}>
          <table className={styles.logsTable}>
            <thead>
              <tr>
                <th>Time</th>
                <th>Type</th>
                <th>Severity</th>
                <th>User</th>
                <th>Action</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className={styles.logTime}>
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td>
                    <span className={`${styles.logTypeBadge} ${getLogTypeClass(log.type)}`}>
                      {getLogTypeIcon(log.type)}
                      <span style={{ marginLeft: '4px' }}>{log.type}</span>
                    </span>
                  </td>
                  <td>
                    <span className={`${styles.severityBadge} ${getSeverityClass(log.severity)}`}>
                      {log.severity}
                    </span>
                  </td>
                  <td>
                    <div style={{ fontWeight: 500 }}>{log.user}</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{log.role}</div>
                  </td>
                  <td style={{ fontWeight: 500 }}>{log.action}</td>
                  <td className={styles.logMessage}>{log.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <Pagination
          currentPage={pagination.currentPage}
          totalPages={pagination.totalPages}
          totalItems={pagination.totalLogs}
          itemsPerPage={pagination.limit}
          onPageChange={onPageChange}
          showInfo={false}
          className={styles.logsPagination}
        />
      </div>
    </div>
  );
};

export default LogTable;
