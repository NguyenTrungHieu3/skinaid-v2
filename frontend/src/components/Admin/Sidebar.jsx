import React from 'react';
import { LuActivity } from 'react-icons/lu';
import "../../assets/styles/admin/Sidebar.scss"

export default function Sidebar({ menuItems, currentPage, onPageChange }) {
  return (
    <div className="admin-sidebar">
      <div className="admin-sidebar-header">
        <div className="admin-sidebar-brand">
          <div className="admin-sidebar-icon">
            <LuActivity />
          </div>
          <div className="admin-sidebar-brand-text">
            <h1>SkinAid</h1>
            <p>Admin Portal</p>
          </div>
        </div>
      </div>

      <nav className="admin-sidebar-nav">
        <ul>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <li key={item.id}>
                <button
                  onClick={() => onPageChange(item.id)}
                  className={isActive ? 'active' : ''}
                >
                  <Icon />
                  <span>{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="admin-sidebar-footer">
        <div className="admin-sidebar-status">
          <p>System Status</p>
          <p>All systems operational</p>
          <div className="admin-status-indicator">
            <div className="status-dot"></div>
            <span>Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}
