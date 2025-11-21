import { useState, useEffect } from 'react';
import {
  getDashboardOverview,
  getWoundTypeDistribution,
  getSeverityStats,
  getSystemLogs
} from '../../services/adminService';
import type {
  DashboardOverview,
  WoundTypeItem,
  SeverityStatsItem,
  SystemLogItem
} from '../../types/admin';
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
  const [systemLogs, setSystemLogs] = useState<SystemLogItem[]>([]);
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
        getSystemLogs(10)
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
        setSystemLogs(logsRes.data.logs);
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

  // Helper to map system logs
  const mapSystemLogs = (logs: SystemLogItem[]) => {
    const severityMap: Record<string, 'low' | 'medium' | 'high'> = {
      'info': 'low',
      'debug': 'low',
      'warning': 'medium',
      'error': 'high',
      'low': 'low',
      'medium': 'medium',
      'high': 'high'
    };

    return logs.map(log => ({
      type: log.type as 'error' | 'success' | 'info',
      severity: severityMap[log.severity.toLowerCase()] || severityMap[log.type?.toLowerCase()] || 'low',
      message: log.message,
      time: log.time || new Date(log.timestamp || Date.now()).toLocaleString()
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

      <DashboardLogs logs={mapSystemLogs(systemLogs)} />
    </div>
  );
}
