import { useState, useEffect } from 'react';
import { getSystemLogs } from '../../services/adminService';
import LogFilters from './components/LogFilters';
import LogTable from './components/LogTable';
import styles from './AdminLogs.module.css';

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

export default function AdminLogs() {
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [filters, setFilters] = useState({
    search: '',
    type: 'all',
    severity: 'all',
    dateRange: 'all'
  });
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const logsPerPage = 10;

  // Fetch system logs
  useEffect(() => {
    fetchSystemLogs();
  }, []);

  const fetchSystemLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await getSystemLogs(50);
      
      if (response.success && response.data) {
        const fetchedLogs = response.data.logs || [];
        // Map backend logs to frontend Log interface if necessary
        // Assuming backend returns compatible structure for now, or mapping basic fields
        const mappedLogs = fetchedLogs.map((log: { [key: string]: unknown }) => ({
          id: (log.id as string) || Math.random().toString(36).substr(2, 9),
          action: (log.action as string) || 'Unknown Action',
          user: (log.user as string) || 'System',
          role: (log.role as string) || 'System',
          timestamp: (log.timestamp as string) || new Date().toISOString(),
          details: (log.message as string) || (log.details as string) || '',
          type: (log.type as 'error' | 'warning' | 'info' | 'success') || 'info',
          severity: (log.severity as 'high' | 'medium' | 'low') || 'low',
          ip: (log.ip as string) || '-'
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

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  // Filter logs
  const filteredLogs = logs.filter(log => {
    const matchesSearch = 
      log.details.toLowerCase().includes(filters.search.toLowerCase()) ||
      log.action.toLowerCase().includes(filters.search.toLowerCase()) ||
      log.user.toLowerCase().includes(filters.search.toLowerCase());
    const matchesType = filters.type === 'all' || log.type === filters.type;
    const matchesSeverity = filters.severity === 'all' || log.severity === filters.severity;
    
    // Date range filtering could be added here
    
    return matchesSearch && matchesType && matchesSeverity;
  });

  // Pagination calculations
  const totalPages = Math.ceil(filteredLogs.length / logsPerPage);
  const indexOfLastLog = currentPage * logsPerPage;
  const indexOfFirstLog = indexOfLastLog - logsPerPage;
  const currentLogs = filteredLogs.slice(indexOfFirstLog, indexOfLastLog);

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
          <h1>System Logs</h1>
          <p>View and manage system logs</p>
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
          logs={currentLogs}
          isLoading={loading}
          error={error}
          pagination={{
            currentPage,
            totalPages,
            totalLogs: filteredLogs.length,
            limit: logsPerPage
          }}
          onPageChange={handlePageChange}
        />
      </div>

      {/* Security Alert */}
      <div className={`${styles.adminCard} ${styles.securityAlert}`}>
        <div className={styles.alertContent}>
          <svg className={styles.alertIcon} width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          </svg>
          <div className={styles.alertText}>
            <p className={styles.alertTitle}>Security Notice</p>
            <p className={styles.alertDescription}>
              This system is monitored. Unauthorized access or misuse will be logged and reported.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
