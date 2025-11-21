import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import styles from './DashboardCharts.module.css';

import type { WoundTypeItem, SeverityStatsItem } from '../../../types/admin';

interface DashboardChartsProps {
  woundTypeData: WoundTypeItem[];
  severityStats: SeverityStatsItem[];
}

export default function DashboardCharts({ woundTypeData, severityStats }: DashboardChartsProps) {
  return (
    <div className={`${styles.adminChartList} ${styles.mt24}`}>
      {/* Wound Type Distribution Chart */}
      <div className={styles.adminChartCard}>
        <div className={styles.adminChartHeader}>
          <div className={styles.adminChartInfo}>
            <h3 className={styles.adminChartTitle}>Wound Type Distribution</h3>
            <p className={styles.adminChartDescription}>Breakdown of wound classifications</p>
          </div>
        </div>
        <div className={styles.adminChartContent}>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={woundTypeData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }: { name: string; percent: number }) => `${name} ${(percent * 100).toFixed(1)}%`}
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
          <div className={styles.woundLegend}>
            {woundTypeData.map((item) => (
              <div key={item.name} className={styles.woundLegendItem}>
                <div className={styles.woundLegendColor} style={{ backgroundColor: item.color }}></div>
                <span className={styles.woundLegendName}>{item.name}</span>
                <span>{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Severity Level Stats Chart */}
      <div className={styles.adminChartCard}>
        <div className={styles.adminChartHeader}>
          <div className={styles.adminChartInfo}>
            <h3 className={styles.adminChartTitle}>Severity Level Stats</h3>
            <p className={styles.adminChartDescription}>Distribution of wound severity</p>
          </div>
        </div>
        <div className={styles.adminChartContent}>
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
                formatter={(value: number, _name: string, props: { payload?: { name: string } }) => {
                  return [`${value} cases`, props.payload?.name];
                }}
                labelFormatter={(label: string) => `Severity: ${label}`}
              />
              <Bar dataKey="value" fill="#1E9378" radius={[8, 8, 0, 0]}>
                {severityStats.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          {/* Custom Legend */}
          <div className={styles.woundLegend} style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '24px',
            marginTop: '20px',
            flexWrap: 'wrap'
          }}>
            {severityStats.map((item) => (
              <div key={item.name} className={styles.woundLegendItem} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <div className={styles.woundLegendColor} style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '2px',
                  backgroundColor: item.color
                }}></div>
                <span className={styles.woundLegendName} style={{
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
  );
}
