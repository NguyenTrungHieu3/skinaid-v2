import { useState } from 'react';
import { Users, FileText, Shield, LayoutGrid, Database } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import AdminDashboard from '../components/admin/AdminDashboard';
import UserManagement from '../components/admin/UserManagement';
import FirstAidManagement from '../components/admin/FirstAidManagement';
import AdminLogs from '../components/admin/AdminLogs';
import ModelManagement from '../components/admin/ModelManagement';
import Sidebar from '../components/admin/Sidebar';
import TopBar from '../components/admin/TopBar';
import styles from './AdminPage.module.css';

export default function AdminPage() {
  const { t } = useTranslation();
  const [currentPage, setCurrentPage] = useState('dashboard');

  const menuItems = [
    { id: 'dashboard', label: t('admin.sidebar.dashboard'), icon: LayoutGrid },
    { id: 'users', label: t('admin.sidebar.user_management'), icon: Users },
    { id: 'firstaid', label: t('admin.sidebar.first_aid_guidance'), icon: FileText },
    { id: 'models', label: t('admin.sidebar.model_management'), icon: Database },
    { id: 'logs', label: t('admin.sidebar.admin_logs'), icon: Shield },
  ];

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <AdminDashboard onNavigate={setCurrentPage} />;
      case 'users':
        return <UserManagement />;
      case 'firstaid':
        return <FirstAidManagement />;
      case 'models':
        return <ModelManagement />;
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
