import { useState } from "react";
import styles from "./HistorySidebar.module.css";
import { Search, Filter } from "lucide-react";
import LogoPlaceholder from "../../assets/images/general/logo_placeholder.png";
import type { HistoryEvent } from "./TimelineVirtualized";
import { useTranslation } from "react-i18next";

interface HistorySidebarProps {
  events: HistoryEvent[];
  onSearchFilter: (filteredEvents: HistoryEvent[]) => void;
}

const HistorySidebar: React.FC<HistorySidebarProps> = ({
  events,
  onSearchFilter,
}) => {
  const { t } = useTranslation();

  const [searchQuery, setSearchQuery] = useState("");

  // --- THAY ĐỔI 1: Để mặc định là rỗng để hiển thị label gốc ---
  const [activeFilter, setActiveFilter] = useState("");

  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const filters = [
    t("history.date_filters.1_day"),
    t("history.date_filters.3_days"),
    t("history.date_filters.7_days"),
    t("history.date_filters.1_month"),
    t("history.date_filters.newest"),
    t("history.date_filters.oldest"),
    // Bạn có thể thêm nút "Tất cả" để reset nếu muốn
    // t("history.date_filters.all"),
  ];

  const filterEvents = (query: string, selectedFilter: string) => {
    let filtered = [...events];

    // 1. Search filter
    if (query.trim()) {
      filtered = filtered.filter(
        (event) =>
          event.title.toLowerCase().includes(query.toLowerCase()) ||
          event.status.toLowerCase().includes(query.toLowerCase())
      );
    }

    // --- THAY ĐỔI 2: Chỉ lọc ngày/sắp xếp nếu CÓ chọn filter ---
    if (selectedFilter) {
      // Handle date filters
      const now = new Date();
      const daysToSubtract: Record<string, number> = {
        [t("history.date_filters.1_day")]: 1,
        [t("history.date_filters.3_days")]: 3,
        [t("history.date_filters.7_days")]: 7,
        [t("history.date_filters.1_month")]: 30,
      };

      if (daysToSubtract[selectedFilter]) {
        const days = daysToSubtract[selectedFilter];
        const startDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

        filtered = filtered.filter((event) => {
          const eventDate = new Date(event.date);
          return eventDate >= startDate;
        });
      }

      // Handle sorting filters
      if (selectedFilter === t("history.date_filters.newest")) {
        filtered.sort(
          (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
        );
      }

      if (selectedFilter === t("history.date_filters.oldest")) {
        filtered.sort(
          (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
        );
      }
    }

    return filtered;
  };

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    const filtered = filterEvents(query, activeFilter);
    onSearchFilter(filtered);
  };

  // Handle date filter change
  const handleFilterChange = (filter: string) => {
    // Nếu bấm vào filter đang chọn -> có thể bỏ chọn (tùy chọn)
    // Ở đây ta cứ set filter mới
    setActiveFilter(filter);
    const filtered = filterEvents(searchQuery, filter);
    onSearchFilter(filtered);
    setIsFilterOpen(false);
  };

  return (
    <div className={styles.sidebarContainer}>
      <div className={styles.topControlsWrapper}>
        {/* 1. Thanh tìm kiếm */}
        <div className={styles.searchBar}>
          <input
            type="text"
            placeholder={t("history.search_placeholder")}
            value={searchQuery}
            onChange={handleSearchChange}
          />
          <Search size={20} className={styles.searchIcon} />
        </div>

        {/* 2. Bộ lọc theo ngày */}
        <div className={styles.filterSection}>
          <div className={styles.filterHeader}>
            {/* --- THAY ĐỔI 3: Hiển thị tên Filter nếu có, ngược lại hiện label mặc định --- */}
            <span className={activeFilter ? styles.activeLabel : ""}>
              {activeFilter || t("history.filter_label")}
            </span>

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
                  onClick={() => handleFilterChange(filter)}
                >
                  {filter}
                </button>
              ))}

              {/* Nút Reset (Tùy chọn: Để quay về trạng thái "Lọc" ban đầu) */}
              <button
                className={styles.filterButton}
                onClick={() => handleFilterChange("")}
                style={{
                  borderTop: "1px solid #eee",
                  marginTop: "4px",
                  color: "#666",
                }}
              >
                {t("history.date_filters.all") || "Bỏ lọc"}
              </button>
            </div>
          )}
        </div>
      </div>

      <div className={styles.logoWrapper}>
        <img
          src={LogoPlaceholder}
          alt="SkinAid Logo"
          className={styles.realLogo}
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              "https://placehold.co/150x150/f0f0f0/b0bec5?text=Logo";
          }}
        />
      </div>
    </div>
  );
};

export default HistorySidebar;
