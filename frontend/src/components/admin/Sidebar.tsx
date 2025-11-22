import { type ElementType } from 'react';
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
  return (
    <div className={styles.adminSidebar}>
      <div className={styles.adminSidebarHeader}>
        <div className={styles.adminSidebarBrand}>
          <img className={styles.logoSkinaid} src={Logo} alt="" />
          <div className={styles.adminSidebarBrandText}>
            <h1>Skin<span>Aid</span></h1>
            <p>Admin Portal</p>
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
          <p>System Status</p>
          <p>All systems operational</p>
          <div className={styles.adminStatusIndicator}>
            <div className={styles.statusDot}></div>
            <span>Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}
