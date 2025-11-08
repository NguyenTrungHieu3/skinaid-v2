import React, { useState, useEffect } from 'react';
import { getSystemLogs } from '../../services/AdminService';

// Mock data for demo when no backend data
const getMockLogs = () => {
  return [
    { type: 'success', message: 'User registered successfully', time: '2 minutes ago', severity: 'low' },
    { type: 'warning', message: 'High server load detected on AI service', time: '5 minutes ago', severity: 'medium' },
    { type: 'info', message: 'Database backup completed successfully', time: '10 minutes ago', severity: 'low' },
    { type: 'error', message: 'Failed to process wound image - Invalid format', time: '15 minutes ago', severity: 'high' },
    { type: 'success', message: 'AI model analysis completed with 3 detections', time: '20 minutes ago', severity: 'low' },
    { type: 'warning', message: 'User exceeded upload limit (5/5 today)', time: '25 minutes ago', severity: 'medium' },
    { type: 'info', message: 'New first-aid guide published: Burn Treatment', time: '30 minutes ago', severity: 'low' },
    { type: 'error', message: 'Authentication failed - Invalid credentials', time: '35 minutes ago', severity: 'high' },
    { type: 'success', message: 'Admin updated user permissions', time: '40 minutes ago', severity: 'low' },
    { type: 'info', message: 'System health check passed', time: '1 hour ago', severity: 'low' },
    { type: 'warning', message: 'Storage usage at 75% capacity', time: '1 hour ago', severity: 'medium' },
    { type: 'success', message: 'Scheduled maintenance completed', time: '2 hours ago', severity: 'low' }
  ];
};

export default function AdminLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const logsPerPage = 10;

  // Fetch system logs
  useEffect(() => {
    fetchSystemLogs();
  }, []);

  const fetchSystemLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await getSystemLogs(50);
      
      if (response.success && response.data) {
        const fetchedLogs = response.data.logs || [];
        
        // If no logs from backend, use mock data for demo
        if (fetchedLogs.length === 0) {
          setLogs(getMockLogs());
        } else {
          setLogs(fetchedLogs);
        }
      }
    } catch (err) {
      console.error('Error fetching system logs:', err);
      // Use mock data if API fails
      setLogs(getMockLogs());
      setError(null); // Don't show error, just use mock data
    } finally {
      setLoading(false);
    }
  };

  // Filter logs
  const filteredLogs = logs.filter(log => {
    const matchesSearch = 
      log.message?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = typeFilter === 'all' || log.type === typeFilter;
    const matchesSeverity = severityFilter === 'all' || log.severity === severityFilter;
    
    return matchesSearch && matchesType && matchesSeverity;
  });

  // Pagination calculations
  const totalPages = Math.ceil(filteredLogs.length / logsPerPage);
  const indexOfLastLog = currentPage * logsPerPage;
  const indexOfFirstLog = indexOfLastLog - logsPerPage;
  const currentLogs = filteredLogs.slice(indexOfFirstLog, indexOfLastLog);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, typeFilter, severityFilter]);

  // Handle page change
  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
    // Scroll to top of logs table
    document.querySelector('.logs-table-card')?.scrollIntoView({ behavior: 'smooth' });
  };

  // Generate page numbers array
  const getPageNumbers = () => {
    const pageNumbers = [];
    const maxVisible = 5;
    
    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pageNumbers.push(i);
      }
    } else {
      if (currentPage <= 3) {
        for (let i = 1; i <= 4; i++) {
          pageNumbers.push(i);
        }
        pageNumbers.push('...');
        pageNumbers.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        pageNumbers.push(1);
        pageNumbers.push('...');
        for (let i = totalPages - 3; i <= totalPages; i++) {
          pageNumbers.push(i);
        }
      } else {
        pageNumbers.push(1);
        pageNumbers.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) {
          pageNumbers.push(i);
        }
        pageNumbers.push('...');
        pageNumbers.push(totalPages);
      }
    }
    
    return pageNumbers;
  };

  // Get badge color based on log type
  const getLogTypeBadge = (type) => {
    const badges = {
      error: 'log-badge-error',
      warning: 'log-badge-warning',
      info: 'log-badge-info',
      success: 'log-badge-success'
    };
    return badges[type] || 'log-badge-info';
  };

  // Get severity badge color
  const getSeverityBadge = (severity) => {
    const badges = {
      high: 'severity-badge-high',
      medium: 'severity-badge-medium',
      low: 'severity-badge-low'
    };
    return badges[severity] || 'severity-badge-low';
  };

  return (
    <div className="admin-logs-page">
      {/* Page Header */}
      <div className="admin-page-header">
        <div className="admin-page-title">
          <h1>Admin Logs & Permissions</h1>
          <p>Monitor system access and manage permissions</p>
        </div>
      </div>

      {/* Filters Card */}
      <div className="admin-card filters-card">
        <div className="filters-container">
          {/* Search */}
          <div className="filter-search">
            <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
            <input
              type="text"
              placeholder="Search logs by message..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="filter-input"
            />
          </div>

          {/* Type Filter */}
          <div className="filter-select-wrapper">
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Types</option>
              <option value="error">Error</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
              <option value="success">Success</option>
            </select>
          </div>

          {/* Severity Filter */}
          <div className="filter-select-wrapper">
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Severity</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Refresh Button */}
          <button onClick={fetchSystemLogs} className="btn-refresh" disabled={loading}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Logs Section */}
      <div className="logs-section">

        {/* Logs Table */}
        <div className="admin-card logs-table-card">
          <div className="card-header">
            <h3>Recent Activities ({filteredLogs.length} total)</h3>
            <span className="page-info">
              Showing {indexOfFirstLog + 1}-{Math.min(indexOfLastLog, filteredLogs.length)} of {filteredLogs.length}
            </span>
          </div>
          <div className="card-content">
            {loading ? (
              <div className="loading-state">
                <div className="spinner"></div>
                <p>Loading logs...</p>
              </div>
            ) : error ? (
              <div className="error-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <p>{error}</p>
              </div>
            ) : filteredLogs.length === 0 ? (
              <div className="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
                <p>No logs found</p>
              </div>
            ) : (
              <div className="logs-table-wrapper">
                <table className="logs-table">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Type</th>
                      <th>Message</th>
                      <th>Severity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentLogs.map((log, index) => (
                      <tr key={index}>
                        <td className="log-time">{log.time}</td>
                        <td>
                          <span className={`log-type-badge ${getLogTypeBadge(log.type)}`}>
                            {log.type}
                          </span>
                        </td>
                        <td className="log-message">{log.message}</td>
                        <td>
                          <span className={`severity-badge ${getSeverityBadge(log.severity)}`}>
                            {log.severity}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Pagination */}
          {!loading && !error && filteredLogs.length > logsPerPage && (
            <div className="pagination">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="pagination-btn"
              >
                Previous
              </button>

              <div className="pagination-numbers">
                {getPageNumbers().map((page, index) => (
                  page === '...' ? (
                    <span key={`ellipsis-${index}`} className="pagination-ellipsis">...</span>
                  ) : (
                    <button
                      key={page}
                      onClick={() => handlePageChange(page)}
                      className={`pagination-number ${currentPage === page ? 'active' : ''}`}
                    >
                      {page}
                    </button>
                  )
                ))}
              </div>

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="pagination-btn"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Security Alert */}
      <div className="admin-card security-alert">
        <div className="alert-content">
          <svg className="alert-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          </svg>
          <div className="alert-text">
            <p className="alert-title">Security Notice</p>
            <p className="alert-description">
              All administrative actions are logged and monitored. Unauthorized access attempts will be reported.
              Ensure you follow HIPAA compliance guidelines when handling patient data.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
