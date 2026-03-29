import { Search } from 'lucide-react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
  return (
    <div className={styles.adminCard}>
      <div className={styles.userFilters}>
        <div className={styles.searchBox}>
          <Search className={styles.searchIcon} size={18} />
          <input
            type="text"
            placeholder={t('admin.user_filters.search_placeholder')}
            value={search}
            onChange={onSearchChange}
          />
        </div>

        <select
          className={styles.filterSelect}
          value={role}
          onChange={onRoleChange}
        >
          <option value="">{t('admin.user_filters.all_roles')}</option>
          <option value="user">{t('admin.user_filters.roles.user')}</option>
          <option value="admin">{t('admin.user_filters.roles.admin')}</option>
        </select>

        <select
          className={styles.filterSelect}
          value={status}
          onChange={onStatusChange}
        >
          <option value="">{t('admin.user_filters.all_status')}</option>
          <option value="active">{t('admin.user_filters.status.active')}</option>
          <option value="inactive">{t('admin.user_filters.status.inactive')}</option>
        </select>
      </div>
    </div>
  );
};

export default UserFilters;
