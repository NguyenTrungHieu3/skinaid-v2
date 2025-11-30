import React from 'react';
import {
  AlertCircle,
  CheckCircle,
  Info,
  AlertTriangle,
  Loader,
  Eye
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
  onViewDetails: (log: Log) => void;
}

const LogTable: React.FC<LogTableProps> = ({
  logs,
  isLoading,
  error,
  pagination,
  onPageChange,
  onViewDetails
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

  const getRoleBadgeClass = (role: string) => {
    const roleClasses: Record<string, string> = {
      user: styles.roleBadgeGray,
      admin: styles.roleBadgePurple
    };
    return roleClasses[role.toLowerCase()] || styles.roleBadgeGray;
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
                <th>User</th>
                <th>Role</th>
                <th>Action</th>
                <th>Details</th>
                <th style={{ width: '80px', textAlign: 'center' }}>View Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className={styles.logTime}>
                    {new Date(log.timestamp + 'Z').toLocaleString('vi-VN', {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                      hour12: true
                    })}
                  </td>
                  <td>
                    <span className={`${styles.logTypeBadge} ${getLogTypeClass(log.type)}`}>
                      {getLogTypeIcon(log.type)}
                      <span style={{ marginLeft: '4px' }}>{log.type}</span>
                    </span>
                  </td>
                  <td className={styles.userCell}>
                    {log.user}
                  </td>
                  <td>
                    <span className={`${styles.roleBadge} ${getRoleBadgeClass(log.role)}`}>
                      {log.role}
                    </span>
                  </td>
                  <td className={styles.standardCell}>{log.action}</td>
                  <td className={`${styles.logMessage} ${styles.standardCell}`}>
                    <div style={{
                      maxWidth: '200px',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {log.details}
                    </div>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      className={styles.viewButton}
                      onClick={() => onViewDetails(log)}
                      title="View Details"
                    >
                      <Eye size={18} />
                    </button>
                  </td>
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
