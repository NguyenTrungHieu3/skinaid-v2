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
  onChange: (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => void;
  type?: string;
  options?: { value: string; label: string }[]; // Thêm options cho select
}

const InfoField = ({
  icon,
  label,
  value,
  editable,
  onChange,
  type = "text",
  options,
}: InfoFieldProps) => (
  <div className={styles.infoField}>
    <label>
      {icon && <span className={styles.infoIcon}>{icon}</span>} {label}
    </label>
    {editable ? (
      type === "select" && options ? (
        <select
          value={value}
          onChange={onChange}
          className={styles.inlineInput}
        >
          <option value="">-- Chọn --</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      ) : (
        <input
          type={type}
          value={value}
          onChange={onChange}
          className={styles.inlineInput}
        />
      )
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
  const [validationErrors, setValidationErrors] = useState<
    Record<string, string>
  >({});

  // SỬA LỖI 1: Thêm 'gender' vào state
  const [formData, setFormData] = useState({
    fullName: "",
    phone: "",
    dob: "",
    address: "",
    gender: "", // <-- ĐÃ THÊM LẠI
  });

  const [originalData, setOriginalData] = useState(formData);

  const validateForm = (data: typeof formData) => {
    const errors: Record<string, string> = {};

    // Full Name
    if (data.fullName.trim() && !/^[a-zA-ZÀ-ỹ\s]+$/.test(data.fullName)) {
      errors.fullName = t("personalInfo.validation.fullName_invalid");
    } else if (data.fullName.length < 2) {
      errors.fullName = t("personalInfo.validation.fullName_too_short");
    }

    // BUG-03 FIX: Phone is optional — only validate format when user has typed something
    if (data.phone.trim()) {
      if (!/^[0-9]+$/.test(data.phone)) {
        errors.phone = t("personalInfo.validation.phone_invalid");
      } else if (!/^0\d{9}$/.test(data.phone)) {
        errors.phone = t("personalInfo.validation.phone_format");
      }
    }

    // Date of Birth
    if (data.dob) {
      const inputDate = new Date(data.dob);
      const today = new Date();

      // 1. Kiểm tra ngày có hợp lệ không (Valid Date)
      if (isNaN(inputDate.getTime())) {
        errors.dob = t("personalInfo.validation.dob_invalid");
      }
      // 2. Kiểm tra ngày tương lai (Không được lớn hơn hôm nay)
      else if (inputDate > today) {
        errors.dob = t("personalInfo.validation.dob_future");
      }
    }

    // Gender
    const validGender = ["male", "female", ""];
    if (!validGender.includes(data.gender)) {
      errors.gender = t("personalInfo.validation.gender_invalid");
    }

    // Address
    if (data.address && data.address.trim().length < 5) {
      errors.address = t("personalInfo.validation.address_too_short");
    }

    return errors;
  };

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
            fullName: profile.full_name || "", // Không dùng user_name làm fallback
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
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
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
        // Hiển thị chi tiết lỗi validation từ server
        const errorMessage =
          err.response?.data?.message || "Failed to save profile.";
        const errorDetail = err.response?.data?.error_details;

        // Nếu có chi tiết lỗi validation (như gender không hợp lệ)
        if (errorDetail) {
          const detailedError =
            typeof errorDetail === "string"
              ? errorDetail
              : JSON.stringify(errorDetail);
          setApiError(`${errorMessage}: ${detailedError}`);
        } else {
          setApiError(errorMessage);
        }
      } else {
        setApiError("An unexpected error occurred.");
      }
    }
  };

  const handleSaveBasic = () => {
    const errors = validateForm(formData);

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return; // Không gọi API nếu có lỗi
    }

    setValidationErrors({}); // Xóa lỗi cũ

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
    setValidationErrors({}); // Xóa lỗi cũ
    setApiError("");
    setApiSuccess("");
  };
  const handleCancelBasic = () => {
    setFormData(originalData);
    setIsEditingBasic(false);
    setApiError("");
    setApiSuccess("");
    setValidationErrors({}); // Xóa lỗi cũ
  };

  if (isLoading) {
    return <div className={styles.infoCard}>Loading profile...</div>;
  }

  // Hàm helper để lấy text hiển thị cho Gender
  const getGenderLabel = (genderValue: string) => {
    if (genderValue === "male") return t("personalInfo.male");
    if (genderValue === "female") return t("personalInfo.female");
    return genderValue; // Fallback nếu rỗng hoặc giá trị lạ
  };

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
              <button type="button" className={styles.editBtn} onClick={handleEditBasic}>
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
            {validationErrors.fullName && (
              <p className={styles.errorText}>{validationErrors.fullName}</p>
            )}
            <InfoField
              icon={<FaPhone />}
              label={t("personalInfo.phone")}
              value={formData.phone}
              editable={isEditingBasic}
              onChange={handleChange("phone")}
            />
            {validationErrors.phone && (
              <p className={styles.errorText}>{validationErrors.phone}</p>
            )}
            <InfoField
              icon={<FaCalendarDay />}
              label={t("personalInfo.dob")}
              value={formData.dob}
              editable={isEditingBasic}
              onChange={handleChange("dob")}
              type="date" // <-- THÊM DÙNG NÀY
            />
            {validationErrors.dob && (
              <p className={styles.errorText}>{validationErrors.dob}</p>
            )}
            {/* THÊM LẠI TRƯỜNG GENDER VÀO JSX */}
            <InfoField
              icon={<FaVenusMars />}
              label={t("personalInfo.gender")}
              // Logic hiển thị thông minh:
              // Nếu đang sửa (isEditingBasic) -> hiện giá trị gốc (male/female) để select box binding đúng
              // Nếu đang xem -> hiện text đã dịch (Nam/Nữ)
              value={
                isEditingBasic
                  ? formData.gender
                  : getGenderLabel(formData.gender)
              }
              editable={isEditingBasic}
              onChange={handleChange("gender")}
              type="select"
              options={[
                { value: "male", label: t("personalInfo.male") },
                { value: "female", label: t("personalInfo.female") },
              ]}
            />
            {validationErrors.gender && (
              <p className={styles.errorText}>{validationErrors.gender}</p>
            )}
            <InfoField
              icon={<FaMapMarkerAlt />}
              label={t("personalInfo.address")}
              value={formData.address}
              editable={isEditingBasic}
              onChange={handleChange("address")}
            />
            {validationErrors.address && (
              <p className={styles.errorText}>{validationErrors.address}</p>
            )}

            {isEditingBasic && (
              <div className={styles.action}>
                <button
                  type="button"
                  className={styles.btnCancel}
                  onClick={handleCancelBasic}
                >
                  {t("personalInfo.cancel_button")}
                </button>
                <button type="button" className={styles.btnSave} onClick={handleSaveBasic}>
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
