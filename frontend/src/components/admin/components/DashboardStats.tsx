import { Users, Image, TrendingUp, Activity, Target } from 'lucide-react';
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

export default function DashboardStats({ overview, period }: DashboardStatsProps) {
  if (!overview) return null;



  const getPeriodLabel = (p: string) => {
    switch (p) {
      case 'day': return 'yesterday';
      case 'week': return 'last week';
      case 'month': return 'last month';
      case 'year': return 'last year';
      case 'all': return 'previous period';
      default: return 'last period';
    }
  };

  const periodLabel = getPeriodLabel(period);

  return (
    <div className={`${styles.adminCardList} ${styles.mt24}`}>
      <div className={`${styles.adminCard} ${styles.adminCardGradientCyan}`}>
        <div className={styles.adminCardHeader}>
          <h3 className={styles.adminCardTitle}>Total Users</h3>
          <div className={`${styles.adminCardIcon} ${styles.iconCyan}`}>
            <Users />
          </div>
        </div>
        <div className={styles.adminCardContent}>
          <div className={styles.adminCardValue}>{overview.total_users.toLocaleString()}</div>
          <p className={`${styles.adminCardChange} ${styles.changeCyan}`}>
            <TrendingUp />
            <span>+{overview.growth_rate}% from {periodLabel}</span>
          </p>
          <div className={styles.adminCardInfo}>
            <p>New Users: <span>{overview.new_users_this_month || 0}</span></p>
          </div>
        </div>
      </div>

      <div className={`${styles.adminCard} ${styles.adminCardGradientBlue}`}>
        <div className={styles.adminCardHeader}>
          <h3 className={styles.adminCardTitle}>Total Uploads</h3>
          <div className={`${styles.adminCardIcon} ${styles.iconBlue}`}>
            <Image />
          </div>
        </div>
        <div className={styles.adminCardContent}>
          <div className={styles.adminCardValue}>{overview.total_images.toLocaleString()}</div>
          <p className={`${styles.adminCardChange} ${styles.changeBlue}`}>
            <TrendingUp />
            <span>+{overview.image_growth_rate}% from {periodLabel}</span>
          </p>
          <div className={styles.adminCardInfo}>
            <p>New uploads: <span>{overview.new_uploads_week || 0}</span></p>
          </div>
        </div>
      </div>

      <div className={`${styles.adminCard} ${styles.adminCardGradientPurple}`}>
        <div className={styles.adminCardHeader}>
          <h3 className={styles.adminCardTitle}>Total Detections</h3>
          <div className={`${styles.adminCardIcon} ${styles.iconPurple}`}>
            <Activity />
          </div>
        </div>
        <div className={styles.adminCardContent}>
          <div className={styles.adminCardValue}>{overview.total_detections.toLocaleString()}</div>
          <p className={`${styles.adminCardChange} ${styles.changePurple}`}>
            <TrendingUp />
            <span>+{overview.detection_growth_rate}% from {periodLabel}</span>
          </p>
          <div className={styles.adminCardInfo}>
            <p>New detection: <span>{overview.new_detections_week || 0}</span></p>
          </div>
        </div>
      </div>

      <div className={`${styles.adminCard} ${styles.adminCardGradientRose}`}>
        <div className={styles.adminCardHeader}>
          <h3 className={styles.adminCardTitle}>Model Accuracy</h3>
          <div className={`${styles.adminCardIcon} ${styles.iconRose}`}>
            <Target />
          </div>
        </div>
        <div className={styles.adminCardContent}>
          <div className={styles.adminCardValue}>{overview.model_accuracy.toFixed(1)}%</div>
          <p className={`${styles.adminCardChange} ${overview.accuracy_trend >= 0 ? styles.changeRose : styles.changeDecline}`}>
            <TrendingUp />
            <span>{overview.accuracy_trend >= 0 ? '+' : ''}{overview.accuracy_trend.toFixed(1)}% from {periodLabel}</span>
          </p>
          <div className={styles.adminCardInfo}>
            <p>High confidence: <span>{overview.high_confidence_detections || 0}</span></p>
          </div>
        </div>
      </div>
    </div>
  );
}
