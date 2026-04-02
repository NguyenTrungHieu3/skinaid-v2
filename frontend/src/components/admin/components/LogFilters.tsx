import { Search, RefreshCw } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import styles from './LogFilters.module.css';

interface LogFiltersProps {
  filters: {
    search: string;
    logType: string;
    level: string;
    role: string;
    dateRange: string;
  };
  onFilterChange: (key: string, value: string) => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}

const LogFilters: React.FC<LogFiltersProps> = ({
  filters,
  onFilterChange,
  onRefresh,
  isRefreshing
}) => {
  const { t } = useTranslation();
  return (
    <div className={styles.filtersCard}>
      <div className={styles.filtersContainer}>
        <div className={styles.filterSearch}>
          <Search className={styles.searchIcon} size={20} />
          <input
            type="text"
            placeholder={t('admin.logs.filters.search_placeholder')}
            value={filters.search}
            onChange={(e) => onFilterChange('search', e.target.value)}
            className={styles.filterInput}
          />
        </div>

        <div className={styles.filterSelectWrapper}>
          <select
            value={filters.logType}
            onChange={(e) => onFilterChange('logType', e.target.value)}
            className={styles.filterSelect}
          >
            <option value="all">{t('admin.logs.filters.all_log_types')}</option>
            <option value="admin_action">{t('admin.logs.filters.log_types.admin_action')}</option>
            <option value="user_activity">{t('admin.logs.filters.log_types.user_activity')}</option>
            <option value="system_error">{t('admin.logs.filters.log_types.system_error')}</option>
          </select>
        </div>

        <div className={styles.filterSelectWrapper}>
          <select
            value={filters.level}
            onChange={(e) => onFilterChange('level', e.target.value)}
            className={styles.filterSelect}
          >
            <option value="all">{t('admin.logs.filters.all_levels')}</option>
            <option value="info">{t('admin.logs.filters.levels.info')}</option>
            <option value="success">{t('admin.logs.filters.levels.success')}</option>
            <option value="warning">{t('admin.logs.filters.levels.warning')}</option>
            <option value="error">{t('admin.logs.filters.levels.error')}</option>
          </select>
        </div>

        <div className={styles.filterSelectWrapper}>
          <select
            value={filters.role}
            onChange={(e) => onFilterChange('role', e.target.value)}
            className={styles.filterSelect}
          >
            <option value="all">{t('admin.logs.filters.all_roles')}</option>
            <option value="admin">{t('admin.logs.filters.roles.admin')}</option>
            <option value="user">{t('admin.logs.filters.roles.user')}</option>
            <option value="guest">{t('admin.logs.filters.roles.guest')}</option>
          </select>
        </div>

        <div className={styles.filterSelectWrapper}>
          <select
            value={filters.dateRange}
            onChange={(e) => onFilterChange('dateRange', e.target.value)}
            className={styles.filterSelect}
          >
            <option value="all">{t('admin.dashboard.periods.all_time')}</option>
            <option value="today">{t('admin.dashboard.periods.today')}</option>
            <option value="7days">{t('admin.dashboard.periods.last_7_days')}</option>
            <option value="30days">{t('admin.dashboard.periods.last_30_days')}</option>
          </select>
        </div>

        <button
          className={styles.btnRefresh}
          onClick={onRefresh}
          disabled={isRefreshing}
        >
          <RefreshCw size={18} className={isRefreshing ? styles.spinner : ''} />
          {t('admin.logs.filters.refresh')}
        </button>
      </div>
    </div>
  );
};

export default LogFilters;
