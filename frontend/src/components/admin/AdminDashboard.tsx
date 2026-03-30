import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  getDashboardOverview,
  getWoundTypeDistribution,
  getSeverityStats,
  getWeeklyActivity,
} from "../../services/adminService";
import { getDashboardRecentLogs } from "../../services/auditService";
import type {
  DashboardOverview,
  WoundTypeItem,
} from "../../types/admin";

import DashboardStats from "./components/DashboardStats";
import DashboardCharts from "./components/DashboardCharts";
import DashboardLogs from "./components/DashboardLogs";
import styles from "./AdminDashboard.module.css";

interface AdminDashboardProps {
  onNavigate?: (page: string) => void;
}

export default function AdminDashboard({ onNavigate }: AdminDashboardProps) {
  const { t } = useTranslation();
  // State
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [period, setPeriod] = useState("month");
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [woundTypeData, setWoundTypeData] = useState<WoundTypeItem[]>([]);
  const [severityStats, setSeverityStats] = useState<Record<string, number>>({});

  const [dashboardLogs, setDashboardLogs] = useState<any[]>([]);
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
      const [overviewRes, woundTypeRes, severityRes, _activityRes, logsRes] =
        await Promise.all([
          getDashboardOverview(period),
          getWoundTypeDistribution(period),
          getSeverityStats(period),
          getWeeklyActivity(),
          getDashboardRecentLogs(5),
        ]);

      if (overviewRes.success && overviewRes.data) {
        setOverview(overviewRes.data);
      }

      if (woundTypeRes.success && woundTypeRes.data) {
        setWoundTypeData(woundTypeRes.data.distribution);
      }

      if (severityRes.success && severityRes.data) {
        // Backend changed: stats array → distribution object
        setSeverityStats(severityRes.data.distribution);
      }

      // Weekly activity data is fetched but only used internally by charts
      // if (activityRes.success && activityRes.data) { }

      // Handle response from /dashboard/logs/recent
      // Format: { logs: [{ type, message, time, severity, source }], total_logs, unresolved_errors }
      if (logsRes.success && logsRes.data) {
        if ('logs' in logsRes.data) {
          setDashboardLogs(logsRes.data.logs);
        }
      }
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
      setError("Failed to load dashboard data. Please try again.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    fetchDashboardData(true);
  };



  // Dashboard logs from /dashboard/logs/recent are already pre-formatted
  // with { type, message, time, severity, source } — no mapping needed

  // Hiển thị giao diện loading khi chờ dữ liệu fetch API
  if (loading) {
    return (
      <div className={styles.adminDashboard}>
        <div className={styles.loadingContainer}>
          <div className={styles.loadingSpinner}></div>
          <p>{t("admin.dashboard.loading")}</p>
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
          <button
            onClick={() => fetchDashboardData()}
            className={styles.retryButton}
          >
            {t("admin.dashboard.retry")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.adminDashboard}>
      <title>{t("title.admin_dashboard")}</title>
      <div className={styles.adminPageHeader}>
        <div className={styles.adminPageTitle}>
          <h1>{t("admin.dashboard.title")}</h1>
          <p>{t("admin.dashboard.subtitle")}</p>
        </div>
        <div className={styles.headerActions}>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className={styles.filterSelect}
            disabled={loading || refreshing}
          >
            <option value="day">{t("admin.dashboard.periods.today")}</option>
            <option value="week">
              {t("admin.dashboard.periods.last_7_days")}
            </option>
            <option value="month">
              {t("admin.dashboard.periods.last_30_days")}
            </option>
            <option value="year">
              {t("admin.dashboard.periods.last_year")}
            </option>
            <option value="all">{t("admin.dashboard.periods.all_time")}</option>
          </select>
          <button
            onClick={handleRefresh}
            className={styles.adminBtnPrimary}
            disabled={refreshing}
          >
            {refreshing
              ? t("admin.dashboard.refreshing")
              : t("admin.dashboard.refresh")}
          </button>
        </div>
      </div>

      <DashboardStats overview={overview} period={period} />

      <DashboardCharts
        woundTypeData={woundTypeData}
        severityStats={severityStats}
      />

      <DashboardLogs
        logs={dashboardLogs}
        onViewAll={onNavigate ? () => onNavigate('logs') : undefined}
      />
    </div>
  );
}
