// src/pages/ProfilePage.tsx
import { useState } from "react";
import styles from "./ProfilePage.module.css"; // File CSS chung

// Import các component
import BannerHeader from "../components/profile/BannerHeader";
import TabBar from "../components/profile/TabBar"; // <-- IMPORT COMPONENT MỚI
import Overview from "../components/profile/Overview";
import PersonalInfo from "../components/profile/PersonalInfo";
import Settings from "../components/profile/Settings";
import { useAuth } from "../contexts/AuthContext";

const ProfilePage = () => {
  const [activeTab, setActiveTab] = useState("overview"); // State vẫn giữ ở trang cha
  const { user } = useAuth();

  const renderTabContent = () => {
    switch (activeTab) {
      case "overview":
        return <Overview />;
      case "personalInfo":
        return <PersonalInfo />;
      case "settings":
        return <Settings />;
      default:
        return <Overview />;
    }
  };

  return (
    <div className={styles.profileContainer}>
      <title>
        {user?.full_name || user?.user_name || "Profile"}
      </title>
      {/* 1. Banner Header (Dùng chung) */}
      <BannerHeader />
      {/* 2. KHỐI NỘI DUNG CHÍNH (Wrapper mới) */}
      {/* Wrapper này sẽ lo việc căn giữa 1200px và kéo đè lên banner */}
      <div className={styles.profileMainWrapper}>
        {/* 2a. Thanh TabBar (đã được đưa ra ngoài) */}
        <TabBar activeTab={activeTab} onTabChange={setActiveTab} />

        {/* 2b. Nội dung (Phần trắng) */}
        {/* Thẻ <main> được giữ lại cho mục đích ngữ nghĩa */}
        <main className={styles.profileContent}>
          <div className={styles.tabContent}>{renderTabContent()}</div>
        </main>
      </div>{" "}
      {/* Đóng .profileMainWrapper */}
    </div>
  );
};

export default ProfilePage;
