import React from 'react';
import { Search, RefreshCw } from 'lucide-react';
import styles from './LogFilters.module.css';

interface LogFiltersProps {
  filters: {
    search: string;
    type: string;
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
  return (
    <div className={styles.filtersCard}>
      <div className={styles.filtersContainer}>
        <div className={styles.filterSearch}>
          <Search className={styles.searchIcon} size={20} />
          <input
            type="text"
            placeholder="Search logs..."
            value={filters.search}
            onChange={(e) => onFilterChange('search', e.target.value)}
            className={styles.filterInput}
          />
        </div>

        <div className={styles.filterSelectWrapper}>
          <select
            value={filters.type}
            onChange={(e) => onFilterChange('type', e.target.value)}
            className={styles.filterSelect}
          >
            <option value="all">All Types</option>
            <option value="success">Success</option>
            <option value="error">Error</option>
          </select>
        </div>

        <div className={styles.filterSelectWrapper}>
          <select
            value={filters.role}
            onChange={(e) => onFilterChange('role', e.target.value)}
            className={styles.filterSelect}
          >
            <option value="all">All Roles</option>
            <option value="admin">Admin</option>
            <option value="user">User</option>
          </select>
        </div>

        <div className={styles.filterSelectWrapper}>
          <select
            value={filters.dateRange}
            onChange={(e) => onFilterChange('dateRange', e.target.value)}
            className={styles.filterSelect}
          >
            <option value="Today">Today</option>
            <option value="Last 7 Days">Last 7 Days</option>
            <option value="Last 30 Days">Last 30 Days</option>
            <option value="all">All Time</option>
          </select>
        </div>

        <button
          className={styles.btnRefresh}
          onClick={onRefresh}
          disabled={isRefreshing}
        >
          <RefreshCw size={18} className={isRefreshing ? styles.spinner : ''} />
          Refresh
        </button>
      </div>
    </div>
  );
};

export default LogFilters;
