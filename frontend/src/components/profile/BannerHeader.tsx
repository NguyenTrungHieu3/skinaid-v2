// src/components/profile/BannerHeader.tsx
import styles from "../../pages/ProfilePage.module.css"; // Dùng file CSS chung
import { FaUser, FaCamera, FaSpinner, FaTrash } from "react-icons/fa";
import { useAuth } from "../../contexts/AuthContext"; // <-- Import AuthContext
import { useTranslation } from "react-i18next";
import {
  uploadAvatarFile,
  updateMyProfile,
  deleteAvatar,
} from "../../services/profileService";
import { useCallback, useRef, useState } from "react";

import Cropper from "react-easy-crop";
import type { Area } from "react-easy-crop"; // Import type Area
import getCroppedImg from "../../utils/cropImage"; // Import hàm utility vừa tạo

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

// Hàm helper để xử lý hiển thị URL ảnh (nếu BE trả về path tương đối)
// Nếu API trả về "/uploads/abc.jpg" và server chạy backend
import { BACKEND_URL } from "../../services/api";

const getImageUrl = (url: string | null | undefined) => {
  if (!url) return null;
  if (url.startsWith("http")) return url;
  // Nếu url là đường dẫn tương đối, nối thêm domain API
  return `${BACKEND_URL}${url}`;
};

const BannerHeader = () => {
  const { user, refreshUser } = useAuth(); // <-- Lấy thông tin user
  const { t, i18n } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // --- STATE CHO CROP IMAGE ---
  const [imageSrc, setImageSrc] = useState<string | null>(null); // Ảnh gốc được chọn
  const [crop, setCrop] = useState({ x: 0, y: 0 }); // Tọa độ pan
  const [zoom, setZoom] = useState(1); // Độ zoom
  const [croppedAreaPixels, setCroppedAreaPixels] = useState<Area | null>(null); // Tọa độ pixel cắt
  const [isCropModalOpen, setIsCropModalOpen] = useState(false); // Đóng/Mở modal

  // Sự kiện click vào icon máy ảnh -> kích hoạt input file ẩn
  const handleCameraClick = () => {
    if (!isUploading && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // XỬ LÝ CHÍNH: Upload -> Lấy Link -> Update Profile
  // const handleFileChange = async (
  //   event: React.ChangeEvent<HTMLInputElement>
  // ) => {
  //   const file = event.target.files?.[0];
  //   if (!file) return;

  //   // 1. Validate loại file (chỉ ảnh)
  //   if (!file.type.startsWith("image/")) {
  //     alert("Vui lòng chọn file định dạng hình ảnh!");
  //     return;
  //   }

  //   // 2. Validate kích thước (ví dụ < 5MB)
  //   if (file.size > 5 * 1024 * 1024) {
  //     alert("Dung lượng file quá lớn (tối đa 5MB)");
  //     return;
  //   }

  //   try {
  //     setIsUploading(true);

  //     // BƯỚC A: Gọi API Upload file lên server
  //     const uploadResponse = await uploadAvatarFile(file);
  //     const avatarUrl = uploadResponse.data.data.url; // Lấy URL từ response BE

  //     if (!avatarUrl) throw new Error("Không nhận được URL ảnh từ server");

  //     // BƯỚC B: Gọi API Update Profile để lưu URL đó vào DB user
  //     await updateMyProfile({ avatar_url: avatarUrl });

  //     // BƯỚC C: Refresh lại thông tin user trong Context để UI tự đổi ảnh
  //     if (refreshUser) {
  //       await refreshUser();
  //     } else {
  //       // Fallback nếu chưa có refreshUser (tải lại trang)
  //       window.location.reload();
  //     }
  //   } catch (error) {
  //     console.error("Upload error:", error);
  //     alert("Có lỗi xảy ra khi cập nhật ảnh đại diện.");
  //   } finally {
  //     setIsUploading(false);
  //     // Reset input để cho phép chọn lại cùng 1 file nếu muốn
  //     if (fileInputRef.current) {
  //       fileInputRef.current.value = "";
  //     }
  //   }
  // };

  // 1. Khi người dùng chọn file -> Đọc file & Mở Modal
  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      alert("Vui lòng chọn file định dạng hình ảnh!");
      return;
    }

    // Đọc file thành URL để hiển thị trong Cropper
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      setImageSrc(reader.result?.toString() || null);
      setIsCropModalOpen(true); // Mở Modal crop
      setZoom(1); // Reset zoom
    });
    reader.readAsDataURL(file);

    // Reset input để chọn lại được file giống cũ nếu cần
    event.target.value = "";
  };

  // 2. Hàm callback khi crop thay đổi (lấy tọa độ pixel)
  const onCropComplete = useCallback(
    (_croppedArea: Area, croppedAreaPixels: Area) => {
      setCroppedAreaPixels(croppedAreaPixels);
    },
    []
  );

  // 3. Khi bấm "Lưu" -> Cắt ảnh -> Upload
  const handleSaveCrop = async () => {
    if (!imageSrc || !croppedAreaPixels) return;

    try {
      setIsUploading(true);
      setIsCropModalOpen(false); // Đóng modal

      // A. Tạo file ảnh đã cắt từ Canvas
      const croppedFile = await getCroppedImg(imageSrc, croppedAreaPixels);

      // B. Upload file đã cắt
      const uploadResponse = await uploadAvatarFile(croppedFile);
      const avatarUrl = uploadResponse.data.data.avatar_url;

      if (!avatarUrl) throw new Error("Không nhận được URL ảnh từ server");

      // C. Update Profile
      await updateMyProfile({ avatar_url: avatarUrl });

      // D. Refresh UI
      if (refreshUser) {
        await refreshUser();
      } else {
        window.location.reload();
      }
    } catch (error) {
      console.error("Upload error:", error);
      alert("Có lỗi xảy ra khi cập nhật ảnh đại diện.");
    } finally {
      setIsUploading(false);
      setImageSrc(null); // Clear ảnh tạm
    }
  };

  // 4. Hủy bỏ crop
  const handleCancelCrop = () => {
    setIsCropModalOpen(false);
    setImageSrc(null);
  };

  // 5. Xóa avatar
  const handleDeleteAvatar = async () => {
    if (!user?.avatar_url) return;

    // Xác nhận trước khi xóa
    const confirmed = window.confirm(t("profile.delete_avatar_confirm") || "Bạn có chắc chắn muốn xóa ảnh đại diện?");
    if (!confirmed) return;

    try {
      setIsDeleting(true);
      await deleteAvatar();

      // Refresh UI
      if (refreshUser) {
        await refreshUser();
      } else {
        window.location.reload();
      }
    } catch (error) {
      console.error("Delete avatar error:", error);
      alert(t("profile.delete_avatar_error") || "Có lỗi xảy ra khi xóa ảnh đại diện.");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <header className={styles.profileBanner}>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
        accept="image/png, image/jpeg, image/jpg"
      />

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
              {/* Layer Loading */}
              {isUploading && (
                <div className={styles.loadingOverlay}>
                  {/* <-- Sử dụng class mới */}
                  <FaSpinner className="fa-spin" color="white" size={24} />
                </div>
              )}

              {/* Hiển thị ảnh */}
              {user?.avatar_url ? (
                <img
                  src={getImageUrl(user.avatar_url) || ""}
                  alt="Avatar"
                  className={styles.avatarImage} // <-- Sử dụng class mới
                  onError={(e) => {
                    e.currentTarget.style.display = "none"; // Logic này giữ nguyên inline vì là thao tác DOM động
                  }}
                />
              ) : (
                <FaUser />
              )}
            </div>

            {/* Nút Camera */}
            <div
              // Kết hợp class: nếu đang uploading thì thêm class uploading
              className={`${styles.cameraIcon} ${isUploading ? styles.uploading : ""
                }`}
              onClick={handleCameraClick}
            >
              <FaCamera />
            </div>

            {/* Nút Xóa Avatar - Chỉ hiển thị khi có avatar */}
            {user?.avatar_url && (
              <div
                className={`${styles.deleteIcon} ${isDeleting ? styles.deleting : ""}`}
                onClick={handleDeleteAvatar}
                title={t("profile.delete_avatar") || "Xóa ảnh đại diện"}
              >
                {isDeleting ? <FaSpinner className="fa-spin" /> : <FaTrash />}
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
          {/* <div className={styles.profileBadges}>
            <div className={`${styles.badgeCard} ${styles.badgeGreen}`}>
              <div className={styles.badgeContent}>
                <span>Total Scans</span>
                <strong>42</strong>
              </div>
              <div className={`${styles.badgeIcon} ${styles.iconBgGreen}`}>
                <FiCamera />
              </div>
            </div> */}

          {/* Badge 2: Last Analysis */}
          {/* <div className={`${styles.badgeCard} ${styles.badgeBlue}`}>
              <div className={styles.badgeContent}>
                <span>Last Analysis</span>
                <strong>Yesterday, 20:15</strong>
              </div>
              <div className={`${styles.badgeIcon} ${styles.iconBgBlue}`}>
                <FaRegClock />
              </div>
            </div>
          </div>*/}
        </div>
      </div>

      {/* --- MODAL CROP ẢNH (Hiển thị khi isCropModalOpen = true) --- */}
      {isCropModalOpen && (
        <div className={styles.cropModalOverlay}>
          <div className={styles.cropModalContent}>
            <h3>Chỉnh sửa ảnh đại diện</h3>

            <div className={styles.cropContainer}>
              <Cropper
                image={imageSrc || ""}
                crop={crop}
                zoom={zoom}
                aspect={1} // Tỉ lệ 1:1
                cropShape="round" // <-- Cắt hình tròn
                showGrid={false}
                onCropChange={setCrop}
                onCropComplete={onCropComplete}
                onZoomChange={setZoom}
              />
            </div>

            <div className={styles.sliderContainer}>
              <label>Zoom</label>
              <input
                type="range"
                value={zoom}
                min={1}
                max={3}
                step={0.1}
                aria-labelledby="Zoom"
                onChange={(e) => setZoom(Number(e.target.value))}
                className={styles.zoomSlider}
              />
            </div>

            <div className={styles.cropActions}>
              <button onClick={handleCancelCrop} className={styles.btnCancel}>
                Hủy
              </button>
              <button onClick={handleSaveCrop} className={styles.btnSave}>
                Lưu ảnh
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

export default BannerHeader;
