import { useState, useEffect } from 'react';
import {
  getDashboardOverview,
  getWoundTypeDistribution,
  getSeverityStats
} from '../../services/adminService';
import { getAuditLogs } from '../../services/auditService';
import type {
  DashboardOverview,
  WoundTypeItem,
  SeverityStatsItem
} from '../../types/admin';
import type { AuditLog } from '../../services/auditService';
import DashboardStats from './components/DashboardStats';
import DashboardCharts from './components/DashboardCharts';
import DashboardLogs from './components/DashboardLogs';
import styles from './AdminDashboard.module.css';

export default function AdminDashboard() {
  // State
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [period, setPeriod] = useState('month');
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [woundTypeData, setWoundTypeData] = useState<WoundTypeItem[]>([]);
  const [severityStats, setSeverityStats] = useState<SeverityStatsItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, [period]);

  // Hàm lấy dữ liệu cho admin dashboard
  const fetchDashboardData = async (isRefresh = false) => {
    // Nếu đã refresh thì sẽ không cần phải hiển thị loading
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    // Gọi hàm lấy data từ API
    try {
      const [overviewRes, woundTypeRes, severityRes, logsRes] = await Promise.all([
        getDashboardOverview(period),
        getWoundTypeDistribution(period),
        getSeverityStats(period),
        getAuditLogs({ limit: 5, page: 1 })
      ]);

      if (overviewRes.success && overviewRes.data) {
        setOverview(overviewRes.data);
      }

      if (woundTypeRes.success && woundTypeRes.data) {
        setWoundTypeData(woundTypeRes.data.distribution);
      }

      if (severityRes.success && severityRes.data) {
        setSeverityStats(severityRes.data.stats);
      }

      if (logsRes.success && logsRes.data) {
        setAuditLogs(logsRes.data.logs);
      }

    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    fetchDashboardData(true);
  };

  // Helper to map audit logs to dashboard log format
  const mapAuditLogs = (logs: AuditLog[]) => {
    return logs.map(log => ({
      type: log.success ? 'success' : 'error' as 'error' | 'success' | 'info',
      severity: log.success ? 'low' : 'high' as 'low' | 'medium' | 'high',
      message: `${log.action} - ${log.resource_type || 'System'}`,
      time: new Date(log.timestamp + 'Z').toLocaleString('vi-VN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      })
    }));
  };

  // Hiển thị giao diện loading khi chờ dữ liệu fetch API
  if (loading) {
    return (
      <div className={styles.adminDashboard}>
        <div className={styles.loadingContainer}>
          <div className={styles.loadingSpinner}></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Nếu có lỗi hiển thị nút retry để load lại dữ liệu 
  if (error) {
    return (
      <div className={styles.adminDashboard}>
        <div className={styles.errorContainer}>
          <p className={styles.errorMessage}>{error}</p>
          <button onClick={() => fetchDashboardData()} className={styles.retryButton}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.adminDashboard}>
      <div className={styles.adminPageHeader}>
        <div className={styles.adminPageTitle}>
          <h1>Admin Dashboard</h1>
          <p>Overview of system performance and statistics</p>
        </div>
        <div className={styles.headerActions}>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className={styles.filterSelect}
            disabled={loading || refreshing}
          >
            <option value="day">Today</option>
            <option value="week">Last 7 Days</option>
            <option value="month">Last 30 Days</option>
            <option value="year">Last Year</option>
            <option value="all">All Time</option>
          </select>
          <button
            onClick={handleRefresh}
            className={styles.adminBtnPrimary}
            disabled={refreshing}
          >
            {refreshing ? 'Refresh...' : 'Refresh Data'}
          </button>
        </div>
      </div>

      <DashboardStats overview={overview} period={period} />

      <DashboardCharts
        woundTypeData={woundTypeData}
        severityStats={severityStats}
      />

      <DashboardLogs logs={mapAuditLogs(auditLogs)} />
    </div>
  );
}
