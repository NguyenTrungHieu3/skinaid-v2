import { useState, useEffect, useRef } from 'react';
import { Users, FileText, Shield, LayoutGrid, Database, BookOpen, ClipboardList, Brain } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import AdminDashboard from '../components/admin/AdminDashboard';
import UserManagement from '../components/admin/UserManagement';
import FirstAidManagement from '../components/admin/FirstAidManagement';
import AdminLogs from '../components/admin/AdminLogs';
import ModelManagement from '../components/admin/ModelManagement';
import RagManagement from '../components/admin/RagManagement';
import QuestionnaireManagement from '../components/admin/QuestionnaireManagement';
import LLMManagement from '../components/admin/LLMManagement';
import Sidebar from '../components/admin/Sidebar';
import TopBar from '../components/admin/TopBar';
import AdminFooter from '../components/admin/AdminFooter';
import styles from './AdminPage.module.css';

export default function AdminPage() {
  const { t, i18n } = useTranslation();
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const prevLang = useRef(i18n.language);

  // Force Vietnamese for admin, restore on leave
  useEffect(() => {
    prevLang.current = i18n.language;
    if (i18n.language !== 'vi') i18n.changeLanguage('vi');
    return () => {
      if (prevLang.current !== 'vi') i18n.changeLanguage(prevLang.current);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const toggleSidebar = () => setSidebarCollapsed((prev) => !prev);

  const menuItems = [
    { id: 'dashboard', label: t('admin.sidebar.dashboard'), icon: LayoutGrid },
    { id: 'users', label: t('admin.sidebar.user_management'), icon: Users },
    { id: 'firstaid', label: t('admin.sidebar.first_aid_guidance'), icon: FileText },
    { id: 'questionnaires', label: 'Bộ câu hỏi', icon: ClipboardList },
    { id: 'models', label: t('admin.sidebar.model_management'), icon: Database },
    { id: 'llm', label: 'Quản lý LLM', icon: Brain },
    { id: 'rag', label: t('admin.sidebar.knowledge_base', 'Cơ sở tri thức'), icon: BookOpen },
    { id: 'logs', label: t('admin.sidebar.admin_logs'), icon: Shield },
  ];

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <AdminDashboard onNavigate={setCurrentPage} />;
        return <AdminDashboard onNavigate={setCurrentPage} />;
      case 'users':
        return <UserManagement />;
      case 'firstaid':
        return <FirstAidManagement />;
      case 'models':
        return <ModelManagement />;
      case 'llm':
        return <LLMManagement />;
      case 'rag':
        return <RagManagement />;
      case 'questionnaires':
        return <QuestionnaireManagement />;
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
        collapsed={sidebarCollapsed}
        onToggle={toggleSidebar}
      />
      <div className={styles.adminMainContent}>
        <TopBar
          onToggleSidebar={toggleSidebar}
          currentPage={currentPage}
          onPageChange={setCurrentPage}
        />
        <main className={styles.adminPageContent}>
          {renderPage()}
        </main>
        <AdminFooter />
      </div>
    </div>
  );
}
