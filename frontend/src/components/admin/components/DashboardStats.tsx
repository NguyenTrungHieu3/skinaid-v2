import { Users, Image, Activity, Target } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import StatCard from '../shared/StatCard';
import styles from './DashboardStats.module.css';

interface OverviewData {
  total_users: number;
  growth_rate: number;
  new_users_this_month: number;
  total_images: number;
  image_growth_rate: number;
  analyzed_images: number;
  total_detections: number;
  detection_growth_rate: number;
  severe_detections: number;
  new_uploads_week: number;
  new_detections_week: number;
  model_accuracy: number;
  accuracy_trend: number;
  high_confidence_detections: number;
}

interface DashboardStatsProps {
  overview: OverviewData | null;
  period: string;
}

export default function DashboardStats({ overview }: DashboardStatsProps) {
  const { t } = useTranslation();
  if (!overview) return null;

  return (
    <div className={`${styles.adminCardList} ${styles.mt24}`}>
      <StatCard
        icon={Users}
        value={overview.total_users.toLocaleString()}
        label={t('admin.dashboard.stats.total_users')}
        color="cyan"
      />
      <StatCard
        icon={Image}
        value={overview.total_images.toLocaleString()}
        label={t('admin.dashboard.stats.total_uploads')}
        color="blue"
      />
      <StatCard
        icon={Activity}
        value={overview.total_detections.toLocaleString()}
        label={t('admin.dashboard.stats.total_detections')}
        color="purple"
      />
      <StatCard
        icon={Target}
        value={`${overview.model_accuracy.toFixed(1)}%`}
        label={t('admin.dashboard.stats.model_accuracy')}
        color="primary"
      />
    </div>
  );
}
