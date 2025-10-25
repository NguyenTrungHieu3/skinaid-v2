import React from 'react';
import { LuBell, LuSearch, LuUser } from 'react-icons/lu';

export default function TopBar() {
  return (
    <header className="admin-topbar">
      <div className="admin-topbar-content">
        <div className="admin-topbar-search">
          <LuSearch />
          <input
            type="text"
            placeholder="Search users, images, logs..."
          />
        </div>

        <div className="admin-topbar-actions">
          <button className="admin-notification-btn">
            <LuBell />
            <span className="notification-badge">3</span>
          </button>

          <div className="admin-user-info">
            <div className="admin-user-text">
              <p>Dr. Sarah Chen</p>
              <p>Administrator</p>
            </div>
            <div className="admin-user-avatar">
              <LuUser />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
