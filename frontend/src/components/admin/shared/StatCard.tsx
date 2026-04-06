import type { ElementType } from 'react';
import styles from './StatCard.module.css';

export type StatCardColor =
  | 'default'
  | 'primary'
  | 'green'
  | 'red'
  | 'blue'
  | 'purple'
  | 'indigo'
  | 'orange'
  | 'yellow'
  | 'cyan';

interface StatCardProps {
  icon: ElementType;
  value: string | number;
  label: string;
  color?: StatCardColor;
}

const colorClassMap: Record<StatCardColor, string> = {
  default:  styles.colorDefault,
  primary:  styles.colorPrimary,
  green:    styles.colorGreen,
  red:      styles.colorRed,
  blue:     styles.colorBlue,
  purple:   styles.colorPurple,
  indigo:   styles.colorIndigo,
  orange:   styles.colorOrange,
  yellow:   styles.colorYellow,
  cyan:     styles.colorCyan,
};

export default function StatCard({ icon: Icon, value, label, color = 'default' }: StatCardProps) {
  return (
    <div className={`${styles.statCard} ${colorClassMap[color]}`}>
      <div className={styles.statIcon}>
        <Icon size={24} />
      </div>
      <div className={styles.statInfo}>
        <div className={styles.statValue}>{value}</div>
        <div className={styles.statLabel}>{label}</div>
      </div>
    </div>
  );
}
