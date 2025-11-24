import React from 'react';
import { Search } from 'lucide-react';
import styles from './UserFilters.module.css';

interface UserFiltersProps {
  search: string;
  onSearchChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  role: string;
  onRoleChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  status: string;
  onStatusChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
}

const UserFilters: React.FC<UserFiltersProps> = ({ 
  search, 
  onSearchChange, 
  role, 
  onRoleChange, 
  status, 
  onStatusChange 
}) => {
  return (
    <div className={styles.adminCard}>
      <div className={styles.userFilters}>
        <div className={styles.searchBox}>
          <Search className={styles.searchIcon} size={18} />
          <input
            type="text"
            placeholder="Search users..."
            value={search}
            onChange={onSearchChange}
          />
        </div>
        
        <select 
          className={styles.filterSelect}
          value={role}
          onChange={onRoleChange}
        >
          <option value="">All Roles</option>
          <option value="user">User</option>
          <option value="admin">Admin</option>
        </select>

        <select 
          className={styles.filterSelect}
          value={status}
          onChange={onStatusChange}
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>
    </div>
  );
};

export default UserFilters;
