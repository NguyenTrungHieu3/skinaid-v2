import React, { useEffect, useState } from 'react';
import { ChevronLeft, AlertTriangle, XCircle, Bell, Loader2, ExternalLink } from 'lucide-react';
import { getNotificationById, markAsRead } from '../../services/notificationService';
import type { NotificationItem } from '../../services/notificationService';
import styles from './NotificationDetail.module.css';

interface NotificationDetailProps {
  notificationId: string;
  onBack: () => void;
}

export default function NotificationDetail({ notificationId, onBack }: NotificationDetailProps) {
  const [notification, setNotification] = useState<NotificationItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAndMarkRead = async () => {
      try {
        setLoading(true);
        // Fetch notification details
        const data = await getNotificationById(notificationId);
        setNotification(data);
        
        // Mark as read if not already read
        if (!data.is_read) {
          await markAsRead(notificationId);
        }
      } catch (error) {
        console.error('Failed to load notification details:', error);
      } finally {
        setLoading(false);
      }
    };
    
    if (notificationId) {
      fetchAndMarkRead();
    }
  }, [notificationId]);

  if (loading) {
    return (
      <div className={styles.loadingState}>
        <Loader2 size={32} className={styles.spin} />
        <p>Đang tải chi tiết thông báo...</p>
      </div>
    );
  }

  if (!notification) {
    return (
      <div className={styles.loadingState}>
        <XCircle size={48} color="#ef4444" />
        <p>Không tìm thấy thông báo hoặc đã bị xóa.</p>
        <button className={styles.backBtn} onClick={onBack}>
          <ChevronLeft size={16} /> Quay lại danh sách
        </button>
      </div>
    );
  }

  // Determine icon and colors based on severity
  let Icon = Bell;
  let iconColor = '#3b82f6';
  let iconBg = '#dbeafe';
  let badgeClass = styles.severityInfo;

  if (notification.severity === 'warning') {
    Icon = AlertTriangle;
    iconColor = '#d97706';
    iconBg = '#fef3c7';
    badgeClass = styles.severityWarning;
  } else if (notification.severity === 'error') {
    Icon = XCircle;
    iconColor = '#dc2626';
    iconBg = '#fee2e2';
    badgeClass = styles.severityError;
  }

  // Format date
  const dateStr = notification.created_at.endsWith("Z") ? notification.created_at : `${notification.created_at}Z`;
  const formattedDate = new Intl.DateTimeFormat('vi-VN', {
    dateStyle: 'full',
    timeStyle: 'medium',
  }).format(new Date(dateStr));

  return (
    <div className={styles.detailContainer}>
      <button className={styles.backBtn} onClick={onBack} style={{ marginBottom: '1rem' }}>
        <ChevronLeft size={16} /> Quay lại
      </button>

      <div className={styles.header}>
        <div className={styles.titleArea}>
          <div className={styles.iconWrap} style={{ background: iconBg, color: iconColor }}>
            <Icon size={24} />
          </div>
          <div>
            <h1 className={styles.title}>{notification.title}</h1>
            <div className={styles.time}>{formattedDate}</div>
          </div>
        </div>
        <span className={`${styles.badge} ${badgeClass}`}>
          {notification.severity.toUpperCase()}
        </span>
      </div>

      <div className={styles.content}>
        {notification.body}
      </div>

      <div className={styles.metadata}>
        <div className={styles.metaItem}>
          <span className={styles.metaLabel}>Loại thông báo</span>
          <span className={styles.metaValue}>{notification.notification_type}</span>
        </div>
        <div className={styles.metaItem}>
          <span className={styles.metaLabel}>Độ ưu tiên</span>
          <span className={styles.metaValue}>{notification.priority}</span>
        </div>
      </div>

      {notification.action_url && (
        <div className={styles.actions}>
          <a 
            href={notification.action_url} 
            className={styles.btnPrimary}
            target="_blank" 
            rel="noopener noreferrer"
          >
            Xem nhật ký / Chi tiết <ExternalLink size={16} />
          </a>
        </div>
      )}
    </div>
  );
}
