import React from "react";
import { Outlet } from "react-router-dom";
import Header from "./Header";
// import Footer from './Footer'; // (Bạn cũng có thể thêm Footer vào đây)
import styles from "./MainLayout.module.css";
const MainLayout: React.FC = () => {
  return (
    <div className={styles.layoutWrapper}>
      <Header />

      {/* 3. <main> NÀY SẼ TỰ ĐỘNG GIÃN RA */}
      <main className={styles.mainContent}>
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout;
