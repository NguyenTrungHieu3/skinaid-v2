import React, { useState, useEffect } from 'react';
import { LuUsers, LuImage, LuTrendingUp, LuInfo } from 'react-icons/lu';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import {
  getDashboardOverview,
  getWoundTypeDistribution,
  getSeverityStats,
  getSystemLogs
} from '../../services/AdminService';

export default function AdminDashboard() {
  // State
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [overview, setOverview] = useState(null);
  const [woundTypeData, setWoundTypeData] = useState([]);
  const [severityStats, setSeverityStats] = useState([]);
  const [systemLogs, setSystemLogs] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Hàm lấy dữ liệu cho admin dashboard
  const fetchDashboardData = async (isRefresh = false) => {
    // Nếu đã refresh thì sẽ không cần phải hiển thị loading
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    
    // Gọi hàm lấy data từ API
    try {
      const [overviewRes, woundTypeRes, severityRes, logsRes] = await Promise.all([
        getDashboardOverview(),
        getWoundTypeDistribution(),
        getSeverityStats(),
        getSystemLogs(10)
      ]);

      if (overviewRes.success) {
        console.log('📊 Dashboard Overview Data:', overviewRes.data);
        console.log('  - Total Users:', overviewRes.data.total_users);
        console.log('  - Active Users:', overviewRes.data.active_users);
        console.log('  - Online Now:', overviewRes.data.online_now);
        setOverview(overviewRes.data);
      }

      if (woundTypeRes.success) {
        setWoundTypeData(woundTypeRes.data.distribution);
      }

      if (severityRes.success) {
        console.log('📈 Severity Stats Data:', severityRes.data.stats);
        setSeverityStats(severityRes.data.stats);
      }

      if (logsRes.success) {
        console.log('📋 System Logs Data:', logsRes.data.logs);
        console.log(`  - Total logs: ${logsRes.data.logs.length}`);
        console.log(`  - Unresolved errors: ${logsRes.data.unresolved_errors}`);
        setSystemLogs(logsRes.data.logs);
      }

    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    fetchDashboardData(true);
  };

  // Giúp chuyển đổi giây(s) sang phút giây (m s)
  const formatSessionDuration = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  // Hiển thị giao diện loading khi chờ dữ liệu fetch API
  if (loading) {
    return (
      <div className="admin-dashboard">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Nếu có lỗi hiển thị nút retry để load lại dữ liệu 
  if (error) {
    return (
      <div className="admin-dashboard">
        <div className="error-container">
          <p className="error-message">{error}</p>
          <button onClick={() => fetchDashboardData()} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-page-header">
        <div className="admin-page-title">
          <h1>Dashboard Overview</h1>
          <p>Monitor system performance and activity</p>
        </div>
        <button 
          onClick={handleRefresh} 
          className="admin-btn-primary"
          disabled={refreshing}
        >
          {refreshing ? 'Refreshing...' : 'Refresh Data'}
        </button>
      </div>

      {overview && (
        <div className="admin-card-list mt-24">
          <div className="admin-card admin-card-gradient-cyan">
            <div className="admin-card-header">
              <h3 className="admin-card-title">Total Users</h3>
              <div className="admin-card-icon icon-cyan">
                <LuUsers />
              </div>
            </div>
            <div className="admin-card-content">
              <div className="admin-card-value">{overview.total_users.toLocaleString()}</div>
              <p className="admin-card-change change-cyan">
                <LuTrendingUp />
                <span>+{overview.growth_rate}% from last month</span>
              </p>
              <div className="admin-card-info">
                <p>New users: <span>{overview.new_users_this_month || 0}</span></p>
              </div>
            </div>
          </div>

          <div className="admin-card admin-card-gradient-blue">
            <div className="admin-card-header">
              <h3 className="admin-card-title">Total Images</h3>
              <div className="admin-card-icon icon-blue">
                <LuImage />
              </div>
            </div>
            <div className="admin-card-content">
              <div className="admin-card-value">{overview.total_images.toLocaleString()}</div>
              <p className="admin-card-change change-blue">
                <LuTrendingUp />
                <span>+{overview.image_growth_rate}% from last month</span>
              </p>
              <div className="admin-card-info">
                <p>Analyzed: <span>{overview.analyzed_images.toLocaleString()}</span></p>
              </div>
            </div>
          </div>

          <div className="admin-card admin-card-gradient-purple">
            <div className="admin-card-header">
              <h3 className="admin-card-title">Active Users</h3>
              <div className="admin-card-icon icon-purple">
                <LuUsers />
              </div>
            </div>
            <div className="admin-card-content">
              <div className="admin-card-value">{overview.active_users}</div>
              <p className="admin-card-change change-purple">
                <LuTrendingUp />
                <span>+{overview.active_users_growth}% this week</span>
              </p>
              <div className="admin-card-grid">
                <div className='admin-card-info'>
                  <p>Online now: <span>{overview.online_now}</span></p>
                </div>
              </div>
            </div>
          </div>

          <div className="admin-card admin-card-gradient-rose">
            <div className="admin-card-header">
              <h3 className="admin-card-title">System Visits</h3>
              <div className="admin-card-icon icon-rose">
                <LuTrendingUp />
              </div>
            </div>
            <div className="admin-card-content">
              <div className="admin-card-value">{overview.total_sessions.toLocaleString()}</div>
              <p className="admin-card-change change-rose">
                <LuTrendingUp />
                <span>+{overview.session_growth_rate}% from last week</span>
              </p>
              <div className="admin-card-info">
                <p>Avg. session: <span>{formatSessionDuration(overview.avg_session_duration_seconds)}</span></p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="admin-chart-list mt-24">
        {/* Wound Type Distribution Chart */}
        <div className="admin-chart-card">
          <div className="admin-chart-header">
            <div className='admin-chart-info'>
              <h3 className="admin-chart-title">Wound Types Distribution</h3>
              <p className='admin-chart-description'>Classification breakdown</p>
            </div>
          </div>
          <div className="admin-chart-content">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={woundTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {woundTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div　className='wound-legend'>
              {woundTypeData.map((item) => (
                <div key={item.name} className='wound-legend-item'>
                  <div className='wound-legend-color' style={{ backgroundColor: item.color }}></div>
                  <span className='wound-legend-name'>{item.name}</span>
                  <span>{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Severity Level Stats Chart */}
        <div className="admin-chart-card">
          <div className="admin-chart-header">
            <div className='admin-chart-info'>
              <h3 className="admin-chart-title">Severity Level Stats</h3>
              <p className='admin-chart-description'>Wound severity distribution</p>
            </div>
          </div>
          <div className="admin-chart-content">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={severityStats}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis 
                  dataKey="name" 
                  stroke="#64748b"
                  tick={{ fontSize: 14, fontWeight: 500 }}
                />
                <YAxis 
                  stroke="#64748b"
                  label={{ 
                    value: 'Number of Cases', 
                    angle: -90, 
                    position: 'insideLeft',
                    style: { fontSize: 14, fontWeight: 500, fill: '#64748b' }
                  }}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                  }}
                  formatter={(value, name, props) => {
                    return [`${value} cases`, props.payload.name];
                  }}
                  labelFormatter={(label) => `Severity: ${label}`}
                />
                <Bar dataKey="value" fill="#1E9378" radius={[8, 8, 0, 0]}>
                  {severityStats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            
            {/* Custom Legend */}
            <div className='wound-legend' style={{ 
              display: 'flex', 
              justifyContent: 'center', 
              gap: '24px', 
              marginTop: '20px',
              flexWrap: 'wrap'
            }}>
              {severityStats.map((item) => (
                <div key={item.name} className='wound-legend-item' style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <div className='wound-legend-color' style={{ 
                    width: '12px',
                    height: '12px',
                    borderRadius: '2px',
                    backgroundColor: item.color 
                  }}></div>
                  <span className='wound-legend-name' style={{
                    fontSize: '14px',
                    fontWeight: 500,
                    color: '#475569'
                  }}>{item.name}</span>
                  <span style={{
                    fontSize: '14px',
                    fontWeight: 600,
                    color: '#1e293b'
                  }}>({item.value})</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="admin-error-logs mt-24">
        <div className="admin-error-logs-header">
          <div>
            <h3 className="admin-error-logs-title">Recent Error Logs & Alerts</h3>
            <p className='admin-error-logs-description'>System notifications and warnings</p>
          </div>
        </div>
        <div className="admin-error-logs-content">
          {systemLogs.map((alert, index) => (
            <div 
              className='admin-error-logs-item'
              key={index} 
              style={{
                backgroundColor: alert.severity === 'high' ? '#fef2f2' : alert.severity === 'medium' ? '#fffbeb' : '#f8fafc',
                borderColor: alert.severity === 'high' ? '#fecaca' : alert.severity === 'medium' ? '#fde68a' : '#e2e8f0'
              }}
            >
              <LuInfo 
              className='admin-error-logs-icon' 
              style={{
                color: alert.severity === 'high' ? '#dc2626' : alert.severity === 'medium' ? '#d97706' : '#64748b',
              }} />
              <div className='admin-error-logs-info'>
                <p className='admin-error-logs-info-header'>{alert.message}</p>
                <p className='admin-error-logs-info-des'>{alert.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
