import { type ElementType } from 'react';
import { useTranslation } from 'react-i18next';
import Logo from '../../assets/images/general/logo.png';
import styles from "./Sidebar.module.css";

interface MenuItem {
  id: string;
  label: string;
  icon: ElementType;
}

interface SidebarProps {
  menuItems: MenuItem[];
  currentPage: string;
  onPageChange: (page: string) => void;
}

export default function Sidebar({ menuItems, currentPage, onPageChange }: SidebarProps) {
  const { t } = useTranslation();

  return (
    <div className={styles.adminSidebar}>
      <div className={styles.adminSidebarHeader}>
        <div className={styles.adminSidebarBrand}>
          <img className={styles.logoSkinaid} src={Logo} alt="" />
          <div className={styles.adminSidebarBrandText}>
            <h1>Skin<span>Aid</span></h1>
            <p>{t('admin.sidebar.portal_title')}</p>
          </div>
        </div>
      </div>

      <nav className={styles.adminSidebarNav}>
        <ul>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <li key={item.id}>
                <button
                  onClick={() => onPageChange(item.id)}
                  className={isActive ? styles.active : ''}
                >
                  <Icon />
                  <span>{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className={styles.adminSidebarFooter}>
        <div className={styles.adminSidebarStatus}>
          <p>{t('admin.sidebar.system_status')}</p>
          <p>{t('admin.sidebar.operational')}</p>
          <div className={styles.adminStatusIndicator}>
            <div className={styles.statusDot}></div>
            <span>{t('admin.sidebar.active')}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
