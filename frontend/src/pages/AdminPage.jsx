import React, { useState } from 'react';
import { LuUsers, LuFileText, LuShield, LuLayoutGrid } from 'react-icons/lu';
import AdminDashboard from '../components/Admin/AdminDashboard';
import UserManagement from '../components/Admin/UserManagement';
import FirstAidManagement from '../components/Admin/FirstAidManagement';
import AdminLogs from '../components/Admin/AdminLogs';
import Sidebar from '../components/Admin/Sidebar';
import TopBar from '../components/Admin/TopBar';
import '../assets/styles/admin/AdminLayout.scss';
import '../assets/styles/admin/Sidebar.scss';
import '../assets/styles/admin/TopBar.scss';
import '../assets/styles/admin/SharedComponents.scss';
import '../assets/styles/admin/AdminDashboard.scss';
import '../assets/styles/admin/UserManagement.scss';
import '../assets/styles/admin/FirstAidManagement.scss';
import '../assets/styles/admin/AdminLogs.scss';
import '../assets/styles/admin/AdminPage.scss'

/**
 * AdminPage - Main entry point for Admin Dashboard
 * Handles navigation state and page rendering
 */
export default function AdminPage() {
  const [currentPage, setCurrentPage] = useState('dashboard');

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LuLayoutGrid },
    { id: 'users', label: 'User Management', icon: LuUsers },
    { id: 'firstaid', label: 'First Aid Guidance', icon: LuFileText },
    { id: 'logs', label: 'Admin Logs', icon: LuShield },
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
    <div className="admin-dashboard-container">
      <Sidebar 
        menuItems={menuItems} 
        currentPage={currentPage} 
        onPageChange={setCurrentPage} 
      />
      <div className="admin-main-content">
        <TopBar />
        <main className="admin-page-content">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}
