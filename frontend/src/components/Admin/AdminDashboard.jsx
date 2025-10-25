import React from 'react';
import { LuUsers, LuImage, LuTrendingUp, LuActivity, LuInfo } from 'react-icons/lu';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const woundTypeData = [
  { name: 'Abrasion', value: 145, color: '#06b6d4' },
  { name: 'Burn', value: 89, color: '#3b82f6' },
  { name: 'Bruise', value: 98, color: '#ec4899' },
];

const activityData = [
  { date: 'Mon', uploads: 45, analyses: 42 },
  { date: 'Tue', uploads: 52, analyses: 48 },
  { date: 'Wed', uploads: 38, analyses: 36 },
  { date: 'Thu', uploads: 65, analyses: 61 },
  { date: 'Fri', uploads: 58, analyses: 55 },
  { date: 'Sat', uploads: 42, analyses: 40 },
  { date: 'Sun', uploads: 35, analyses: 33 },
];

const systemLogs = [
  { type: 'warning', message: 'High server load detected', time: '5 minutes ago', severity: 'medium' },
  { type: 'info', message: 'Model updated to version 2.1.4', time: '1 hour ago', severity: 'low' },
  { type: 'error', message: 'Failed image upload from user #3421', time: '2 hours ago', severity: 'high' },
  { type: 'success', message: 'Daily backup completed successfully', time: '3 hours ago', severity: 'low' },
];

export default function AdminDashboard() {
  return (
    <div className="admin-dashboard">
      <div className="admin-page-header">
        <div className="admin-page-title">
          <h1>Dashboard Overview</h1>
          <p>Monitor system performance and activity</p>
        </div>
      </div>

      <div className="admin-card-list mt-24">
        <div className="admin-card admin-card-gradient-cyan">
          <div className="admin-card-header">
            <h3 className="admin-card-title">Total Users</h3>
            <div className="admin-card-icon icon-cyan">
              <LuUsers />
            </div>
          </div>
          <div className="admin-card-content">
            <div className="admin-card-value">5,247</div>
            <p className="admin-card-change change-cyan">
              <LuTrendingUp />
              <span>+12% from last month</span>
            </p>
            <div className="admin-card-info">
              <p>Active today: <span>342</span></p>
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
            <div className="admin-card-value">12,483</div>
            <p className="admin-card-change change-blue">
              <LuTrendingUp />
              <span>+8% from last month</span>
            </p>
            <div className="admin-card-info">
              <p>Analyzed: <span>11,956</span></p>
            </div>
          </div>
        </div>

        <div className="admin-card admin-card-gradient-purple">
          <div className="admin-card-header">
            <h3 className="admin-card-title">Model Accuracy</h3>
            <div className="admin-card-icon icon-purple">
              <LuActivity />
            </div>
          </div>
          <div className="admin-card-content">
            <div className="admin-card-value">94.2%</div>
            <p className="admin-card-change change-purple">
              <LuTrendingUp />
              <span>+2.1% improvement</span>
            </p>
            <div className="admin-card-grid">
              <div className='admin-card-info'>
                <p>Precision: <span>92.8%</span></p>
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
            <div className="admin-card-value">28,394</div>
            <p className="admin-card-change change-rose">
              <LuTrendingUp />
              <span>+18% from last week</span>
            </p>
            <div className="admin-card-info">
              <p>Avg. session: <span>8m 32s</span></p>
            </div>
          </div>
        </div>
      </div>

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

        {/* Activity Chart */}
        <div className="admin-chart-card">
          <div className="admin-chart-header">
            <div className='admin-chart-info'>
              <h3 className="admin-chart-title">Weekly Activity</h3>
              <p className='admin-chart-description'>Image uploads vs analyses</p>
            </div>
          </div>
          <div className="admin-chart-content">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={activityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                  }} 
                />
                  <Legend 
                    wrapperStyle={{
                      bottom: '-20px'
                    }}
                  />
                <Bar dataKey="uploads" fill="#06b6d4" radius={[8, 8, 0, 0]} />
                <Bar dataKey="analyses" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
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
