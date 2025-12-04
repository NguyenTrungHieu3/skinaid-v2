import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getAuditLogs } from '../../services/auditService';
import LogFilters from './components/LogFilters';
import LogTable from './components/LogTable';
import LogDetailsModal from './components/LogDetailsModal';
import styles from './AdminLogs.module.css';

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
  fullDetails?: any;
}

export default function AdminLogs() {
  const { t } = useTranslation();
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<Log | null>(null);

  // Filters
  const [filters, setFilters] = useState({
    search: '',
    type: 'all',
    role: 'all',
    dateRange: 'all'
  });

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [logsPerPage] = useState(5);
  const [totalCount, setTotalCount] = useState(0);

  // Fetch system logs with server-side pagination
  const fetchSystemLogs = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        limit: logsPerPage,
        offset: (currentPage - 1) * logsPerPage
      };

      // Add search filter
      if (filters.search) {
        params.search = filters.search;
      }

      // Map frontend 'type' to backend 'success'
      if (filters.type === 'success') {
        params.success = true;
      } else if (filters.type === 'error') {
        params.success = false;
      }
      // 'all' = no success filter

      // Add role filter
      if (filters.role !== 'all') {
        params.role_name = filters.role;
      }

      // Map dateRange to start_date
      if (filters.dateRange !== 'all') {
        const now = new Date();
        if (filters.dateRange === 'Today') {
          const startOfDay = new Date(now.setHours(0, 0, 0, 0));
          params.start_date = startOfDay.toISOString();
        } else if (filters.dateRange === 'Last 7 Days') {
          const weekAgo = new Date();
          weekAgo.setDate(weekAgo.getDate() - 7);
          params.start_date = weekAgo.toISOString();
        } else if (filters.dateRange === 'Last 30 Days') {
          const monthAgo = new Date();
          monthAgo.setDate(monthAgo.getDate() - 30);
          params.start_date = monthAgo.toISOString();
        }
      }

      const response = await getAuditLogs(params);

      if (response.success && response.data) {
        const fetchedLogs = response.data.logs || [];
        setTotalCount(response.data.total || fetchedLogs.length);

        const mappedLogs: Log[] = fetchedLogs.map((log: any) => ({
          id: log.audit_action_id,
          action: log.action,
          user: log.user_name || (log.user_id ? `User ${log.user_id.substring(0, 8)}...` : (log.is_guest ? 'Guest' : 'System')),
          email: log.email,
          role: log.role_name || (log.is_guest ? 'Guest' : 'User'),
          timestamp: log.timestamp,
          details: log.error_message || (log.details ? JSON.stringify(log.details) : log.action),
          type: log.success ? 'success' : 'error',
          severity: !log.success ? 'high' : 'low',
          ip: log.ip_address || '-',
          fullDetails: log.details
        }));
        setLogs(mappedLogs);
      }
    } catch (err) {
      console.error('Error fetching system logs:', err);
      setError('Failed to load system logs');
    } finally {
      setLoading(false);
    }
  };

  // Fetch on mount and when filters change (reset to page 1)
  useEffect(() => {
    setCurrentPage(1);
  }, [filters.search, filters.type, filters.role, filters.dateRange]);

  // Fetch when page changes or filters change
  useEffect(() => {
    fetchSystemLogs();
  }, [currentPage, logsPerPage, filters.search, filters.type, filters.role, filters.dateRange]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleViewDetails = (log: Log) => {
    setSelectedLog(log);
  };

  const handleCloseModal = () => {
    setSelectedLog(null);
  };

  // Handle page change
  const handlePageChange = (pageNumber: number) => {
    setCurrentPage(pageNumber);
    // Scroll to top of logs table
    document.querySelector(`.${styles.logsTableCard}`)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className={styles.adminLogsPage}>
      {/* Page Header */}
      <div className={styles.adminPageHeader}>
        <div className={styles.adminPageTitle}>
          <h1>{t('admin.logs.title')}</h1>
          <p>{t('admin.logs.subtitle')}</p>
        </div>
      </div>

      {/* Filters Card */}
      <LogFilters
        filters={filters}
        onFilterChange={handleFilterChange}
        onRefresh={fetchSystemLogs}
        isRefreshing={loading}
      />

      {/* Logs Section */}
      <div className={styles.logsSection}>
        <LogTable
          logs={logs}
          isLoading={loading}
          error={error}
          pagination={{
            currentPage,
            totalPages: Math.ceil(totalCount / logsPerPage),
            totalLogs: totalCount,
            limit: logsPerPage
          }}
          onPageChange={handlePageChange}
          onViewDetails={handleViewDetails}
        />
      </div>

      {/* Security Alert */}
      <div className={`${styles.adminCard} ${styles.securityAlert}`}>
        <div className={styles.alertContent}>
          <svg className={styles.alertIcon} width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          </svg>
          <div className={styles.alertText}>
            <p className={styles.alertTitle}>{t('admin.logs.security_notice')}</p>
            <p className={styles.alertDescription}>
              {t('admin.logs.security_desc')}
            </p>
          </div>
        </div>
      </div>

      {/* Log Details Modal */}
      {selectedLog && (
        <LogDetailsModal
          log={selectedLog}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
}
