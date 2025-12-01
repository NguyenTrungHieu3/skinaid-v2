// src/components/profile/BannerHeader.tsx
import styles from "../../pages/ProfilePage.module.css"; // Dùng file CSS chung
import {
  FaUser,
  FaCamera,
  FaRegClock,
  FaSpinner,
  FaTrash,
  // FaFileMedicalAlt,
  // FaCheckCircle,
  // FaCalendarAlt,
  // FaHeartbeat,
} from "react-icons/fa";
import { useAuth } from "../../contexts/AuthContext"; // <-- Import AuthContext
import { FiCamera } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import { useRef, useState } from "react";
import { uploadAvatar, deleteAvatar } from "../../services/profileService";
import { useToast } from "../../contexts/ToastContext";

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
  const { user, updateUser } = useAuth(); // <-- Lấy thông tin user và updateUser
  const { t, i18n } = useTranslation();
  const toast = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Helper function to get full avatar URL
  const getAvatarUrl = (avatarPath: string | null | undefined): string | null => {
    if (!avatarPath) return null;
    // If already a full URL, return as is
    if (avatarPath.startsWith('http://') || avatarPath.startsWith('https://')) {
      return avatarPath;
    }
    // Convert relative path to absolute URL
    return `http://localhost:8000${avatarPath}`;
  };

  // Handle camera icon click - trigger file input
  const handleCameraClick = () => {
    if (!isUploading) {
      fileInputRef.current?.click();
    }
  };

  // Handle file selection and upload
  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      toast.error("Vui lòng chọn file ảnh (JPEG, PNG, hoặc WEBP)");
      return;
    }

    // Validate file size (5MB)
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error("Kích thước file không được vượt quá 5MB");
      return;
    }

    // Upload file
    setIsUploading(true);
    try {
      const response = await uploadAvatar(file);
      if (response.data.data) {
        toast.success("Upload avatar thành công!");
        // Update user data to reflect avatar change everywhere
        updateUser({ avatar_url: response.data.data.avatar_url });
      }
    } catch (error: any) {
      console.error("Upload avatar failed:", error);
      const errorMessage = error?.response?.data?.message || "Có lỗi xảy ra khi upload avatar";
      toast.error(errorMessage);
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Handle delete avatar
  const handleDeleteAvatar = async () => {
    console.log("[DELETE AVATAR] Function called");

    // No confirmation needed - user can always re-upload
    console.log("[DELETE AVATAR] Starting delete process");
    setIsDeleting(true);
    try {
      console.log("[DELETE AVATAR] Calling API...");
      const response = await deleteAvatar();
      console.log("[DELETE AVATAR] API response:", response);

      toast.success("Đã xóa avatar!");
      // Update user data to remove avatar
      updateUser({ avatar_url: null });
      console.log("[DELETE AVATAR] User data updated");
    } catch (error: any) {
      console.error("[DELETE AVATAR] Error:", error);
      const errorMessage = error?.response?.data?.message || "Có lỗi xảy ra khi xóa avatar";
      toast.error(errorMessage);
    } finally {
      setIsDeleting(false);
      console.log("[DELETE AVATAR] Completed");
    }
  };

  return (
    <header className={styles.profileBanner}>
      <div className={styles.bannerContentWrapper}>
        {/* BÊN TRÁI - AVATAR */}
        <div className={styles.profileLeft}>
          <div className={styles.avatarWrapper}>
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/jpg,image/png,image/webp"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />

            {/* Avatar display */}
            <div className={styles.avatarPlaceholder}>
              {user?.avatar_url ? (
                <img
                  src={getAvatarUrl(user.avatar_url) || ''}
                  alt="User Avatar"
                  className={styles.avatarImage}
                />
              ) : (
                <FaUser />
              )}

              {/* Loading overlay */}
              {(isUploading || isDeleting) && (
                <div className={styles.avatarLoadingOverlay}>
                  <FaSpinner className={styles.spinnerIcon} />
                </div>
              )}
            </div>

            {/* Camera icon - clickable */}
            <div
              className={styles.cameraIcon}
              onClick={handleCameraClick}
              title={isUploading ? "Đang tải lên..." : "Thay đổi avatar"}
            >
              <FaCamera />
            </div>

            {/* Delete icon - only show when user has avatar */}
            {user?.avatar_url && (
              <div
                className={styles.deleteIcon}
                onClick={handleDeleteAvatar}
                title={isDeleting ? "Đang xóa..." : "Xóa avatar"}
              >
                <FaTrash />
              </div>
            )}
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
