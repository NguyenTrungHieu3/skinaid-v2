import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { getAuditLogs } from "../../services/auditService";
import LogFilters from "./components/LogFilters";
import LogTable from "./components/LogTable";
import LogDetailsModal from "./components/LogDetailsModal";
import styles from "./AdminLogs.module.css";

interface Log {
  id: string;
  action: string;
  user: string;
  email?: string;
  role: string;
  timestamp: string;
  description: string;
  type: "error" | "warning" | "info" | "success";
  logType: string; // admin_action / user_activity / system_error
  severity: "high" | "medium" | "low";
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
    search: "",
    logType: "all",   // admin_action / user_activity / system_error
    level: "all",     // success / warning / error
    dateRange: "all",
  });

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [logsPerPage] = useState(20);
  const [totalCount, setTotalCount] = useState(0);

  // Fetch system logs with server-side pagination
  const fetchSystemLogs = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        limit: logsPerPage,
        page: currentPage,
      };

      // Add search filter
      if (filters.search) {
        params.search = filters.search;
      }

      // Map log_type filter
      if (filters.logType !== "all") {
        params.log_type = filters.logType;
      }

      // Map level filter — must stay consistent with badge logic below
      if (filters.level === "success") {
        // "Success" = successful operations (level=info + success=true)
        params.success = true;
      } else if (filters.level === "info") {
        // "Info" = info-level logs that were NOT successful
        params.level = "info";
        params.success = false;
      } else if (filters.level !== "all") {
        params.level = filters.level;
      }

      // Map dateRange to start_date and end_date
      if (filters.dateRange !== "all") {
        const now = new Date();
        const endOfNow = new Date(); // current moment as end boundary
        params.end_date = endOfNow.toISOString();

        if (filters.dateRange === "today") {
          const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
          params.start_date = startOfDay.toISOString();
        } else if (filters.dateRange === "7days") {
          const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          params.start_date = weekAgo.toISOString();
        } else if (filters.dateRange === "30days") {
          const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          params.start_date = monthAgo.toISOString();
        }
      }

      const response = await getAuditLogs(params);

      if (response.success && response.data) {
        const fetchedLogs = response.data.logs || [];
        setTotalCount(response.data.total || fetchedLogs.length);

        const mappedLogs: Log[] = fetchedLogs.map((log: any) => {
          // Use backend level field directly for badge display
          const level = log.level || "info";
          let type: "error" | "warning" | "info" | "success" = "info";
          let severity: "high" | "medium" | "low" = "low";

          // Badge logic: must match filter logic above
          if (level === "error") {
            type = "error";
            severity = "high";
          } else if (level === "warning") {
            type = "warning";
            severity = "medium";
          } else if (log.success === true) {
            // level=info + success=true → "Success" badge
            type = "success";
            severity = "low";
          } else {
            // level=info + success=false → "Info" badge
            type = "info";
            severity = "low";
          }

          return {
            id: log.audit_action_id || log.log_id,
            action: log.action,
            user:
              log.user_name ||
              (log.user_id
                ? `User ${log.user_id.substring(0, 8)}...`
                : log.is_guest
                  ? "Khách"
                  : "Hệ thống"),
            email: log.email,
            role: log.role_name || (log.is_guest ? "Khách" : "Người dùng"),
            timestamp: log.timestamp,
            description: log.description || log.error_message || log.action,
            type,
            logType: log.log_type || "user_activity",
            severity,
            ip: log.ip_address || "-",
            fullDetails: log.details,
          };
        });
        setLogs(mappedLogs);
      }
    } catch (err) {
      setError("Không thể tải nhật ký hệ thống");
    } finally {
      setLoading(false);
    }
  };

  // Track if filters changed to reset page
  const filtersKey = `${filters.search}|${filters.logType}|${filters.level}|${filters.dateRange}`;

  useEffect(() => {
    // When filters change, always fetch from page 1
    setCurrentPage(1);
  }, [filtersKey]);

  useEffect(() => {
    fetchSystemLogs();
  }, [currentPage, filtersKey]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
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
    document
      .querySelector(`.${styles.logsTableCard}`)
      ?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className={styles.adminLogsPage}>
      <title>{t("title.admin_logs")}</title>
      {/* Page Header */}
      <div className={styles.adminPageHeader}>
        <div className={styles.adminPageTitle}>
          <h1>{t("admin.logs.title")}</h1>
          <p>{t("admin.logs.subtitle")}</p>
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
            limit: logsPerPage,
          }}
          onPageChange={handlePageChange}
          onViewDetails={handleViewDetails}
        />
      </div>

      {/* Security Alert */}
      <div className={`${styles.adminCard} ${styles.securityAlert}`}>
        <div className={styles.alertContent}>
          <svg
            className={styles.alertIcon}
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          </svg>
          <div className={styles.alertText}>
            <p className={styles.alertTitle}>
              {t("admin.logs.security_notice")}
            </p>
            <p className={styles.alertDescription}>
              {t("admin.logs.security_desc")}
            </p>
          </div>
        </div>
      </div>

      {/* Log Details Modal */}
      {selectedLog && (
        <LogDetailsModal log={selectedLog} onClose={handleCloseModal} />
      )}
    </div>
  );
}


