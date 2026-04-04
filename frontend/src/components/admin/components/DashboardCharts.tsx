import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useTranslation } from 'react-i18next';
import styles from './DashboardCharts.module.css';

import type { WoundTypeItem } from '../../../types/admin';

interface DashboardChartsProps {
  woundTypeData: WoundTypeItem[];
  severityStats: Record<string, number>;
}

export default function DashboardCharts({ woundTypeData, severityStats }: DashboardChartsProps) {
  const { t } = useTranslation();

  // Convert severity stats object to array for chart
  const severityData = Object.entries(severityStats).map(([name, value]) => {
    const colorMap: Record<string, string> = {
      'mild': '#10b981',
      'moderate': '#f59e0b',
      'severe': '#ef4444'
    };
    return {
      name: name.toLowerCase(),
      value: value,
      color: colorMap[name.toLowerCase()] || '#64748b'
    };
  });

  // Function to translate severity labels
  const translateSeverity = (severity: string) => {
    const severityLower = severity.toLowerCase();
    if (severityLower === 'mild') return t('admin.first_aid_form.options.mild');
    if (severityLower === 'moderate') return t('admin.first_aid_form.options.moderate');
    if (severityLower === 'severe') return t('admin.first_aid_form.options.severe');
    return severity; // fallback to original if not matched
  };

  return (
    <div className={`${styles.adminChartList} ${styles.mt24}`}>
      {/* Wound Type Distribution Chart */}
      <div className={styles.adminChartCard}>
        <div className={styles.adminChartHeader}>
          <div className={styles.adminChartInfo}>
            <h3 className={styles.adminChartTitle}>{t('admin.dashboard.charts.wound_distribution_title')}</h3>
            <p className={styles.adminChartDescription}>{t('admin.dashboard.charts.wound_distribution_desc')}</p>
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
                label={({ name, percent }: { name?: string; percent?: number }) => name && percent !== undefined ? `${name} ${(percent * 100).toFixed(1)}%` : ''}
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
                <span className={styles.woundLegendValue}>({item.value})</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Severity Level Stats Chart */}
      <div className={styles.adminChartCard}>
        <div className={styles.adminChartHeader}>
          <div className={styles.adminChartInfo}>
            <h3 className={styles.adminChartTitle}>{t('admin.dashboard.charts.severity_stats_title')}</h3>
            <p className={styles.adminChartDescription}>{t('admin.dashboard.charts.severity_stats_desc')}</p>
          </div>
        </div>
        <div className={styles.adminChartContent}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={severityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="name"
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12 }}
                tickFormatter={translateSeverity}
              />
              <YAxis
                stroke="#64748b"
                label={{
                  value: t('admin.dashboard.charts.number_of_cases'),
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
                formatter={(value: any, _name: any, props: any) => {
                  return [`${value} ${t('admin.dashboard.charts.cases')}`, props.payload?.name];
                }}
                labelFormatter={(label: any) => `${t('admin.dashboard.charts.severity_label')}: ${translateSeverity(String(label))}`}
              />
              <Bar dataKey="value" fill="#1E9378" radius={[8, 8, 0, 0]}>
                {severityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          {/* Custom Legend */}
          <div className={styles.woundLegend}>
            {severityData.map((item) => (
              <div key={item.name} className={styles.woundLegendItem}>
                <div 
                  className={styles.woundLegendColor} 
                  style={{ backgroundColor: item.color }}
                ></div>
                <span className={styles.woundLegendName}>
                  {translateSeverity(item.name)}
                </span>
                <span className={styles.woundLegendValue}>
                  ({item.value})
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
