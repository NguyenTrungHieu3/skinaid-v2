import React, { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Header from "./Header";
// import Footer from './Footer'; // (Bạn cũng có thể thêm Footer vào đây)
import styles from "./MainLayout.module.css";

export type MainLayoutContextType = {
  setMenuOpen: (open: boolean) => void;
};

const MainLayout: React.FC = () => {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const isMapPage = location.pathname === "/map";

  return (
    <div className={`${styles.layoutWrapper} ${isMapPage ? styles.mapLayout : ""}`}>
      <Header menuOpen={menuOpen} setMenuOpen={setMenuOpen} />

      {/* 3. <main> NÀY SẼ TỰ ĐỘNG GIÃN RA */}
      <main className={styles.mainContent}>
        <Outlet context={{ setMenuOpen } satisfies MainLayoutContextType} />
      </main>
    </div>
  );
};

export default MainLayout;
