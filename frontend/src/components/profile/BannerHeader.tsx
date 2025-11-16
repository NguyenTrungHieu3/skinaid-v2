// src/components/profile/BannerHeader.tsx
import styles from "../../pages/ProfilePage.module.css"; // Dùng file CSS chung
import {
  FaUser,
  FaCamera,
  FaRegClock,
  // FaFileMedicalAlt,
  // FaCheckCircle,
  // FaCalendarAlt,
  // FaHeartbeat,
} from "react-icons/fa";
import { useAuth } from "../../contexts/AuthContext"; // <-- Import AuthContext
import { FiCamera } from "react-icons/fi";
import { useTranslation } from "react-i18next";

const formatDate = (dateString: string | undefined, lang: string) => {
  if (!dateString) return "N/A";
  try {
    // --- SỬA Ở ĐÂY ---
    // Chuyển từ 'en-US' (tháng, năm) sang 'vi-VN' (ngày/tháng/năm)
    return new Date(dateString).toLocaleDateString(lang, {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
    // --- KẾT THÚC SỬA ---
  } catch (e) {
    return "N/A";
  }
};

const BannerHeader = () => {
  const { user } = useAuth(); // <-- Lấy thông tin user
  const { t, i18n } = useTranslation();

  return (
    <header className={styles.profileBanner}>
      <div className={styles.bannerContentWrapper}>
        {/* BÊN TRÁI - AVATAR */}
        <div className={styles.profileLeft}>
          <div className={styles.avatarWrapper}>
            <div className={styles.avatarPlaceholder}>
              <FaUser />
            </div>
            <div className={styles.cameraIcon}>
              <FaCamera />
            </div>
          </div>
        </div>

        {/* BÊN PHẢI - THÔNG TIN + THỐNG KÊ */}
        <div className={styles.profileRight}>
          <div className={styles.profileInfo}>
            {/* Lấy tên user từ Context */}
            <h1>{user?.full_name || user?.user_name || "Loading..."}</h1>
            <p>
              {/* <span>&bull;</span> */}
              <span>
                {t("profile.banner_date")}{" "}
                {formatDate(user?.created_at, i18n.language)}
              </span>
            </p>
          </div>

          {/* 2. KHỐI BADGE MỚI */}
          <div className={styles.profileBadges}>
            {/* Badge 1: Total Scans */}
            <div className={`${styles.badgeCard} ${styles.badgeGreen}`}>
              <div className={styles.badgeContent}>
                <span>Total Scans</span>
                <strong>42</strong>
              </div>
              <div className={`${styles.badgeIcon} ${styles.iconBgGreen}`}>
                <FiCamera />
              </div>
            </div>

            {/* Badge 2: Last Analysis */}
            <div className={`${styles.badgeCard} ${styles.badgeBlue}`}>
              <div className={styles.badgeContent}>
                <span>Last Analysis</span>
                <strong>Yesterday, 20:15</strong>
              </div>
              <div className={`${styles.badgeIcon} ${styles.iconBgBlue}`}>
                <FaRegClock />
              </div>
            </div>
          </div>

          {/* <div className={styles.statsContainer}>
            <div className={styles.statCard}>
              <FaHeartbeat className={styles.statIcon} />
              <div className={styles.statDetails}>
                <span>Active</span>
                <strong>2</strong>
              </div>
            </div>
            <div className={styles.statCard}>
              <FaFileMedicalAlt className={styles.statIcon} />
              <div className={styles.statDetails}>
                <span>Analyses</span>
                <strong>15</strong>
              </div>
            </div>
            <div className={styles.statCard}>
              <FaCheckCircle className={styles.statIcon} />
              <div className={styles.statDetails}>
                <span>Healed</span>
                <strong>8</strong>
              </div>
            </div>
            <div className={styles.statCard}>
              <FaCalendarAlt className={styles.statIcon} />
              <div className={styles.statDetails}>
                <span>Days</span>
                <strong>120</strong>
              </div>
            </div>
          </div> */}
        </div>
      </div>
    </header>
  );
};

export default BannerHeader;
