import React, { useState, useEffect } from "react";
import styles from "../../pages/ProfilePage.module.css";
import {
  FaPen,
  FaUser,
  FaPhone,
  FaCalendarDay,
  FaMapMarkerAlt,
  FaSave,
  FaVenusMars, // Thêm icon
} from "react-icons/fa";
import { useAuth } from "../../contexts/AuthContext";
import { useTranslation } from "react-i18next";
import {
  getMyProfile,
  updateMyProfile,
  type UserProfileUpdate,
} from "../../services/profileService";
import { isAxiosError } from "axios";

// ... (Component InfoField giữ nguyên) ...
interface InfoFieldProps {
  icon?: React.ReactNode;
  label: string;
  value: string;
  editable: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  type?: string;
}

const InfoField = ({
  icon,
  label,
  value,
  editable,
  onChange,
  type = "text",
}: InfoFieldProps) => (
  <div className={styles.infoField}>
    <label>
      {icon && <span className={styles.infoIcon}>{icon}</span>} {label}
    </label>
    {editable ? (
      <input
        type={type}
        value={value}
        onChange={onChange}
        className={styles.inlineInput}
      />
    ) : (
      <div
        className={styles.infoValue}
        style={{
          opacity: !value || value.startsWith("List current") ? 0.6 : 1,
        }}
      >
        {value || "N/A"}
      </div>
    )}
  </div>
);

const PersonalInfo = () => {
  const { user, updateUser } = useAuth(); // Lấy user và hàm updateUser
  const { t } = useTranslation();

  const [isEditingBasic, setIsEditingBasic] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [apiError, setApiError] = useState("");
  const [apiSuccess, setApiSuccess] = useState("");

  // SỬA LỖI 1: Thêm 'gender' vào state
  const [formData, setFormData] = useState({
    fullName: "",
    phone: "",
    dob: "",
    address: "",
    gender: "", // <-- ĐÃ THÊM LẠI
  });

  const [originalData, setOriginalData] = useState(formData);

  useEffect(() => {
    const formatDate = (dateString: string | null) => {
      if (!dateString) return "";
      try {
        return new Date(dateString).toISOString().split("T")[0];
      } catch (e) {
        return "";
      }
    };

    const fetchProfile = async () => {
      if (!user) {
        setIsLoading(false);
        return;
      }
      try {
        setIsLoading(true);
        setApiError("");
        const response = await getMyProfile();
        if (response.data.success) {
          const profile = response.data.data;

          // Thêm 'gender' vào mapping
          const mappedData = {
            fullName: profile.full_name || user.user_name || "",
            phone: profile.phone || "",
            dob: formatDate(profile.date_of_birth),
            address: profile.address || "",
            gender: profile.gender || "", // <-- ĐÃ THÊM LẠI
          };
          setFormData(mappedData);
          setOriginalData(mappedData);
        }
      } catch (err) {
        if (isAxiosError(err)) {
          setApiError(err.response?.data?.message || "Failed to load profile.");
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, [user]);

  const handleChange =
    (field: keyof typeof formData) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setFormData((prev) => ({ ...prev, [field]: e.target.value }));
      if (apiSuccess) setApiSuccess(""); // Xóa thông báo khi user sửa
      if (apiError) setApiError("");
    };

  const handleSave = async (
    dataToSave: UserProfileUpdate,
    setEditingState: (isEditing: boolean) => void
  ) => {
    setApiError("");
    setApiSuccess("");
    try {
      // Gửi 'null' nếu trường là chuỗi rỗng
      const payload: UserProfileUpdate = {
        full_name: dataToSave.full_name || null,
        phone: dataToSave.phone || null,
        date_of_birth: dataToSave.date_of_birth || null,
        address: dataToSave.address || null,
        gender: dataToSave.gender || null, // <-- Thêm 'gender'
      };

      const response = await updateMyProfile(payload); // Gửi payload đã xử lý

      if (response.data.success) {
        const updatedProfile = response.data.data;

        const mappedData = {
          fullName: updatedProfile.full_name || "",
          phone: updatedProfile.phone || "",
          dob: updatedProfile.date_of_birth
            ? new Date(updatedProfile.date_of_birth).toISOString().split("T")[0]
            : "",
          address: updatedProfile.address || "",
          gender: updatedProfile.gender || "", // <-- Thêm 'gender'
        };

        setFormData(mappedData);
        setOriginalData(mappedData);
        setEditingState(false);
        setApiSuccess("Profile updated successfully!");

        setTimeout(() => {
          setApiSuccess("");
        }, 500);

        // Cập nhật AuthContext (để Header cũng thay đổi)
        updateUser({
          full_name: updatedProfile.full_name ?? undefined,
          phone: updatedProfile.phone ?? undefined,
          date_of_birth: updatedProfile.date_of_birth ?? undefined,
          gender: updatedProfile.gender ?? undefined,
          avatar_url: updatedProfile.avatar_url ?? undefined,
        });
      }
    } catch (err) {
      if (isAxiosError(err)) {
        // Hiển thị lỗi từ server (ví dụ: validation 422)
        setApiError(err.response?.data?.message || "Failed to save profile.");
      }
    }
  };

  const handleSaveBasic = () => {
    // SỬA LỖI 2: Thêm 'gender' vào đây
    const dataToUpdate = {
      full_name: formData.fullName,
      phone: formData.phone,
      date_of_birth: formData.dob,
      address: formData.address,
      gender: formData.gender, // <-- ĐÃ THÊM LẠI
    };
    handleSave(dataToUpdate, setIsEditingBasic);
  };

  // Logic Hủy (Cancel)
  const handleEditBasic = () => {
    setOriginalData(formData);
    setIsEditingBasic(true);
    setApiError("");
    setApiSuccess("");
  };
  const handleCancelBasic = () => {
    setFormData(originalData);
    setIsEditingBasic(false);
    setApiError("");
    setApiSuccess("");
  };

  if (isLoading) {
    return <div className={styles.infoCard}>Loading profile...</div>;
  }

  return (
    <div className={styles.personalInfoWrapper}>
      {apiError && <div className={styles.apiErrorMessage}>{apiError}</div>}
      {apiSuccess && (
        <div className={styles.apiSuccessMessage}>{apiSuccess}</div>
      )}
      <div className={styles.infoGrid}>
        {/* BASIC INFORMATION */}
        <div className={styles.infoCard}>
          <div className={styles.cardHeader}>
            <h3>{t("personalInfo.basic_info")}</h3>
            {!isEditingBasic && (
              <button className={styles.editBtn} onClick={handleEditBasic}>
                <FaPen />
              </button>
            )}
          </div>
          <div className={styles.cardBody}>
            <InfoField
              icon={<FaUser />}
              label={t("personalInfo.full_name")}
              value={formData.fullName}
              editable={isEditingBasic}
              onChange={handleChange("fullName")}
            />

            <InfoField
              icon={<FaPhone />}
              label={t("personalInfo.phone")}
              value={formData.phone}
              editable={isEditingBasic}
              onChange={handleChange("phone")}
            />

            <InfoField
              icon={<FaCalendarDay />}
              label={t("personalInfo.dob")}
              value={formData.dob}
              editable={isEditingBasic}
              onChange={handleChange("dob")}
              type="date" // <-- THÊM DÙNG NÀY
            />

            {/* THÊM LẠI TRƯỜNG GENDER VÀO JSX */}
            <InfoField
              icon={<FaVenusMars />}
              label="Gender" // (Bạn có thể thêm key 'personalInfo.gender' vào file translation)
              value={formData.gender}
              editable={isEditingBasic}
              onChange={handleChange("gender")}
            />

            <InfoField
              icon={<FaMapMarkerAlt />}
              label={t("personalInfo.address")}
              value={formData.address}
              editable={isEditingBasic}
              onChange={handleChange("address")}
            />

            {isEditingBasic && (
              <div className={styles.action}>
                <button
                  className={styles.btnCancel}
                  onClick={handleCancelBasic}
                >
                  {t("personalInfo.cancel_button")}
                </button>
                <button className={styles.btnSave} onClick={handleSaveBasic}>
                  <FaSave /> {t("personalInfo.save_button")}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* (Thẻ Medical Information đã được xóa) */}
      </div>
    </div>
  );
};

export default PersonalInfo;
