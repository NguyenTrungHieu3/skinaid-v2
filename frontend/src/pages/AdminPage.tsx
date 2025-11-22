import { useState } from 'react';
import { Users, FileText, Shield, LayoutGrid } from 'lucide-react';
import AdminDashboard from '../components/admin/AdminDashboard';
import UserManagement from '../components/admin/UserManagement';
import FirstAidManagement from '../components/admin/FirstAidManagement';
import AdminLogs from '../components/admin/AdminLogs';
import Sidebar from '../components/admin/Sidebar';
import TopBar from '../components/admin/TopBar';
import styles from './AdminPage.module.css';

export default function AdminPage() {
  const [currentPage, setCurrentPage] = useState('dashboard');

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutGrid },
    { id: 'users', label: 'User Management', icon: Users },
    { id: 'firstaid', label: 'First Aid Guidance', icon: FileText },
    { id: 'logs', label: 'Admin Logs', icon: Shield },
  ];

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <AdminDashboard />;
      case 'users':
        return <UserManagement />;
      case 'firstaid':
        return <FirstAidManagement />;
      case 'logs':
        return <AdminLogs />;
      default:
        return <AdminDashboard />;
    }
  };

  return (
    <div className={styles.adminDashboardContainer}>
      <Sidebar
        menuItems={menuItems}
        currentPage={currentPage}
        onPageChange={setCurrentPage}
      />
      <div className={styles.adminMainContent}>
        <TopBar />
        <main className={styles.adminPageContent}>
          {renderPage()}
        </main>
      </div>
    </div>
  );
}
