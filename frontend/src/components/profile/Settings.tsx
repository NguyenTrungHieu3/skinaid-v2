// src/components/profile/Settings.tsx
import { useState, useEffect } from "react";

import styles from "../../pages/ProfilePage.module.css";
import {
  FaBell,
  FaMoon,
  FaShieldAlt, // <-- Icon mới
} from "react-icons/fa";
import { useTranslation } from "react-i18next";
import ChangePasswordModal from "../auth/ChangePasswordModal";

// LocalStorage key for settings
const SETTINGS_STORAGE_KEY = "skinaid_user_settings";

// Default settings
const defaultSettings = {
  email: true,
  push: false,
  darkMode: false,
};

// Load settings from localStorage
const loadSettings = () => {
  try {
    const saved = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (saved) {
      return { ...defaultSettings, ...JSON.parse(saved) };
    }
  } catch {
    // If parsing fails, return defaults
  }
  return defaultSettings;
};

// Component Toggle Switch
const ToggleSwitch = ({
  id,
  checked,
  onChange,
}: {
  id: string;
  checked?: boolean;
  onChange?: () => void;
}) => (
  <label htmlFor={id} className={styles.switch}>
    <input
      id={id}
      type="checkbox"
      defaultChecked={checked}
      onChange={onChange}
    />
        <span className={styles.slider}></span> {" "}
  </label>
);

const Settings = () => {
  const { t } = useTranslation();
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Initialize settings from localStorage
  const [settings, setSettings] = useState(loadSettings);

  // Save settings to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
    } catch {
      // Silently fail if localStorage is not available
    }
  }, [settings]);

  const handleToggle = (key: keyof typeof settings) => {
    setSettings((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  return (
    <div className={styles.settingsWrapper}>
      <div className={styles.settingsCard}>
        <div className={styles.cardHeader}>
          <h3>
            <FaBell className={styles.cardHeaderIcon} />
            <span>{t("settings.notifications")}</span>
          </h3>
        </div>

        {/* Item 1: Email Notifications */}
        <div className={styles.settingItem}>
          <div className={styles.settingInfo}>
            <h4>{t("settings.email_title")}</h4>
            <p>{t("settings.email_desc")}</p>
          </div>
          <ToggleSwitch
            id="email-toggle"
            checked={settings.email}
            onChange={() => handleToggle("email")}
          />
        </div>

        {/* Item 2: Push Notifications */}
        <div className={styles.settingItem}>
          <div className={styles.settingInfo}>
            <h4>{t("settings.push_nofi_title")}</h4>
            <p>{t("settings.push_nofi_desc")}</p>
          </div>
          <ToggleSwitch
            id="push-toggle"
            checked={settings.push}
            onChange={() => handleToggle("push")}
          />
        </div>

        <div className={styles.cardHeader} style={{ marginTop: "1.5rem" }}>
          <h3>
            <FaShieldAlt className={styles.cardHeaderIcon} />
            <span>{t("settings.security_title")}</span>
          </h3>
        </div>

        {/* Item 4: Change Password (Mới) */}
        <div className={styles.settingItem}>
          <div className={styles.settingInfo}>
            <h4>{t("settings.password_title")}</h4>
            <p>{t("settings.password_desc")}</p>
          </div>
          {/* Đây nên là 1 nút bấm, không phải toggle */}
          <button
            className={styles.languageSelect} // Tái sử dụng style của dropdown
            onClick={() => setIsModalOpen(true)} // Điều hướng
          >
            {t("settings.password_button")}
          </button>
        </div>

        {/* Appearance section */}
        <div className={styles.cardHeader} style={{ marginTop: "1.5rem" }}>
          <h3>
            <FaMoon className={styles.cardHeaderIcon} />
            <span>{t("settings.appearance")}</span>
          </h3>
        </div>

        {/* <div className={styles.settingItem}>
          <div className={styles.settingInfo}>
            <h4>{t("settings.language_title")}</h4>
            <p>{t("settings.language_desc")}</p>
          </div>
          
          <select
            value={i18n.language} // Lấy ngôn ngữ hiện tại
            onChange={handleLanguageChange} // Gọi hàm đổi ngônS ngữ
            className={styles.languageSelect} // (Thêm CSS cho đẹp)
          >
            <option value="en">English</option>
            <option value="vi">Tiếng Việt</option>
          </select>
        </div> */}

        {/* Item 3: Dark Mode */}
        <div className={styles.settingItem}>
          <div className={styles.settingInfo}>
            <h4>{t("settings.mode_title")}</h4>
            <p>{t("settings.mode_desc")}</p>
          </div>
          <ToggleSwitch
            id="dark-mode-toggle"
            checked={settings.darkMode}
            onChange={() => handleToggle("darkMode")}
          />
        </div>
      </div>
      {/* --- 4. RENDER MODAL (Nằm bên ngoài .settingsCard) --- */}
      {isModalOpen && (
        <ChangePasswordModal onClose={() => setIsModalOpen(false)} />
      )}
    </div>
  );
};

export default Settings;
