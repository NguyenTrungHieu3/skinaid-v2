import React from 'react';
import {
  AlertCircle,
  CheckCircle,
  Info,
  AlertTriangle,
  Loader,
  Eye
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import Pagination from '../../common/Pagination';
import styles from './LogTable.module.css';

interface Log {
  id: string;
  action: string;
  user: string;
  role: string;
  timestamp: string;
  description: string;
  type: 'error' | 'warning' | 'info' | 'success';
  logType: string;
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
  const { t } = useTranslation();

  // Function to translate role
  const translateRole = (role: string) => {
    const roleLower = role.toLowerCase();
    if (['user', 'admin', 'guest'].includes(roleLower)) {
      return t(`admin.logs.filters.roles.${roleLower}`);
    }
    return role;
  };

  // Function to translate action
  const translateAction = (action: string) => {
    const key = `admin.dashboard.logs.actions.${action}`;
    const translated = t(key);
    return translated !== key ? translated : action;
  };

  // Function to translate log type badge
  const translateLevel = (type: string) => {
    const typeLower = type.toLowerCase();
    if (['success', 'error', 'info', 'warning'].includes(typeLower)) {
      return t(`admin.logs.types.${typeLower}`);
    }
    return type;
  };

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
          <p>{t('admin.logs.table.loading')}</p>
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
            {t('admin.logs.table.try_again')}
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
          <p>{t('admin.logs.table.no_logs')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.logsTableCard}>
      <div className={styles.cardHeader}>
        <h3>{t('admin.logs.table.title')}</h3>
        <span className={styles.pageInfo}>
          {t('admin.logs.table.showing', {
            start: ((pagination.currentPage - 1) * pagination.limit) + 1,
            end: Math.min(pagination.currentPage * pagination.limit, pagination.totalLogs),
            total: pagination.totalLogs
          })}
        </span>
      </div>

      <div className={styles.cardContent}>
        <div className={styles.logsTableWrapper}>
          <table className={styles.logsTable}>
            <thead>
              <tr>
                <th>{t('admin.logs.table.headers.time')}</th>
                <th>{t('admin.logs.table.headers.type')}</th>
                <th>{t('admin.logs.table.headers.username')}</th>
                <th>{t('admin.logs.table.headers.role')}</th>
                <th>{t('admin.logs.table.headers.action')}</th>
                <th>{t('admin.logs.table.headers.description')}</th>
                <th style={{ width: '80px', textAlign: 'center' }}>{t('admin.logs.table.headers.view_details')}</th>
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
                      <span style={{ marginLeft: '4px' }}>{translateLevel(log.type)}</span>
                    </span>
                  </td>
                  <td className={styles.userCell}>
                    {log.user}
                  </td>
                  <td>
                    <span className={`${styles.roleBadge} ${getRoleBadgeClass(log.role)}`}>
                      {translateRole(log.role)}
                    </span>
                  </td>
                  <td className={styles.standardCell}>{translateAction(log.action)}</td>
                  <td className={`${styles.logMessage} ${styles.standardCell}`}>
                    <div style={{
                      maxWidth: '250px',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {log.description}
                    </div>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      className={styles.viewButton}
                      onClick={() => onViewDetails(log)}
                      title={t('admin.logs.table.headers.view_details')}
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
