import React, { useState } from "react";
import styles from "./HistorySidebar.module.css";
// Thêm icon 'SlidersHorizontal' cho thanh trượt
import { Search, Filter, SlidersHorizontal, Pointer } from "lucide-react";
import LogoPlaceholder from "../../assets/images/general/logo_placeholder.png";

const HistorySidebar = () => {
  const [activeFilter, setActiveFilter] = useState("7 ngày");
  // State mới cho thanh trượt, ví dụ mặc định là 80%
  const [accuracy, setAccuracy] = useState(80);

  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [isAccuracyOpen, setIsAccuracyOpen] = useState(false);

  const filters = ["7 ngày", "2 tuần", "1 tháng", "3 tháng"];

  return (
    <div className={styles.sidebarContainer}>
      <div className={styles.topControlsWrapper}>
        {/* 1. Thanh tìm kiếm (Không đổi) */}
        <div className={styles.searchBar}>
          <input type="text" placeholder="Tìm kiếm" />
          <Search size={20} className={styles.searchIcon} />
        </div>

        {/* 2. Bộ lọc (Không đổi) */}
        <div className={styles.filterSection}>
          <div className={styles.filterHeader}>
            <span>Lọc</span>
            <Filter
              size={15}
              className={styles.filterIcon}
              onClick={() => setIsFilterOpen((prev) => !prev)}
            />
          </div>

          {isFilterOpen && (
            <div className={styles.filterOptions}>
              {filters.map((filter) => (
                <button
                  key={filter}
                  className={`${styles.filterButton} ${
                    activeFilter === filter ? styles.activeFilter : ""
                  }`}
                  onClick={() => setActiveFilter(filter)}
                >
                  {filter}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 3. KHỐI MỚI: Thanh trượt độ chính xác */}
        <div className={styles.accuracySection}>
          <div className={styles.accuracyHeader}>
            <span>Độ chính xác</span>
            <SlidersHorizontal
              size={15}
              className={styles.accuracyIcon}
              onClick={() => setIsAccuracyOpen((prev) => !prev)}
            />
          </div>
          {isAccuracyOpen && (
            <div className={styles.accuracyBody}>
              <input
                type="range"
                min="0"
                max="100"
                value={accuracy}
                className={styles.accuracySlider}
                onChange={(e) => setAccuracy(Number(e.target.value))}
              />
              <div className={styles.accuracyValue}>Trên {accuracy}%</div>
            </div>
          )}
        </div>
      </div>

      {/* KHỐI MỚI: Logo Placeholder */}
      <div className={styles.logoWrapper}>
        {/* THAY THẾ BẰNG ẢNH THẬT CỦA BẠN */}
        <img
          // Bạn có thể đặt ảnh trong folder /public
          // và gọi nó như '/logo-skinaid.png'
          src={LogoPlaceholder} // <-- THAY BẰNG LINK ẢNH CỦA BẠN
          alt="SkinAid Logo"
          className={styles.realLogo}
          onError={(e) => {
            // Dự phòng nếu ảnh của bạn bị lỗi
            (e.target as HTMLImageElement).src =
              "https://placehold.co/150x150/f0f0f0/b0bec5?text=Logo";
          }}
        />
      </div>
    </div>
  );
};

export default HistorySidebar;
