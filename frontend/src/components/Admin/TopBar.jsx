import React, { useState, useEffect } from 'react';
import { LuLogOut } from 'react-icons/lu';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../../contexts/ToastContext';

export default function TopBar() {
  const navigate = useNavigate();
  const toast = useToast();
  const [userInfo, setUserInfo] = useState({
    displayName: 'Admin User',
    role: 'Administrator',
    email: ''
  });
  const [showLogoutMenu, setShowLogoutMenu] = useState(false);

  useEffect(() => {
    // Get user data from localStorage
    const userData = localStorage.getItem('user');
    if (userData) {
      try {
        const user = JSON.parse(userData);
        
        // Extract display name (prefer display_name, fallback to email)
        const displayName = user.display_name || user.email?.split('@')[0] || 'Admin User';
        
        // Extract role (get first role or default to 'User')
        let role = 'User';
        if (user.roles && user.roles.length > 0) {
          const userRole = user.roles[0].toLowerCase();
          // Map role to display name
          const roleMap = {
            'admin': 'Administrator',
            'moderator': 'Moderator',
            'user': 'User'
          };
          role = roleMap[userRole] || userRole.charAt(0).toUpperCase() + userRole.slice(1);
        }
        
        setUserInfo({
          displayName,
          role,
          email: user.email || ''
        });
      } catch (error) {
        console.error('Error parsing user data:', error);
      }
    }
  }, []);

  // Close logout menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showLogoutMenu && !event.target.closest('.admin-user-info')) {
        setShowLogoutMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showLogoutMenu]);

  // Handle logout
  const handleLogout = () => {
    // Confirm before logout
    if (window.confirm('Are you sure you want to logout?')) {
      // Clear all auth data from localStorage
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      
      // Show success message
      toast.success('Logged out successfully');
      
      // Redirect to signin page
      navigate('/signin');
    }
  };

  // Get initials from display name for avatar
  const getInitials = (name) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <header className="admin-topbar">
      <div className="admin-topbar-content">
        <div className="admin-topbar-title">
          <h2>Admin Dashboard</h2>
        </div>

        <div className="admin-topbar-actions">
          <div 
            className="admin-user-info" 
            title={userInfo.email}
            onClick={() => setShowLogoutMenu(!showLogoutMenu)}
          >
            <div className="admin-user-text">
              <p>{userInfo.displayName}</p>
              <p>{userInfo.role}</p>
            </div>
            <div className="admin-user-avatar">
              {getInitials(userInfo.displayName)}
            </div>
            
            {/* Logout Menu */}
            {showLogoutMenu && (
              <div className="logout-menu">
                <div className="logout-menu-header">
                  <p className="logout-menu-name">{userInfo.displayName}</p>
                  <p className="logout-menu-email">{userInfo.email}</p>
                </div>
                <div className="logout-menu-divider"></div>
                <button className="logout-menu-button" onClick={handleLogout}>
                  <LuLogOut size={16} />
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
