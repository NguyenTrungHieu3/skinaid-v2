import { useState } from "react";
import styles from "./HistorySidebar.module.css";
import { Search, Filter} from "lucide-react";
import LogoPlaceholder from "../../assets/images/general/logo_placeholder.png";
import type { HistoryEvent } from "./TimelineVirtualized";

// Define props interface
interface HistorySidebarProps {
  events: HistoryEvent[];
  onSearchFilter: (filteredEvents: HistoryEvent[]) => void;
}

const HistorySidebar: React.FC<HistorySidebarProps> = ({ events, onSearchFilter }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("7 ngày");

  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const filters = [
    "1 ngày",
    "3 ngày",
    "7 ngày",
    "1 tháng",
    "3 tháng",
    "6 tháng",
    "1 năm",
  ];

  // Filter events based on search query and date filter
  const filterEvents = (query: string, dateFilter: string) => {
    let filtered = events;

    // Filter by date range
    const now = new Date();
    const daysToSubtract: { [key: string]: number } = {
      "1 ngày": 1,
      "3 ngày": 3,
      "7 ngày": 7,
      "1 tháng": 30,
      "3 tháng": 90,
      "6 tháng": 180,
      "1 năm": 365,
    };

    const days = daysToSubtract[dateFilter] || 7;
    const startDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

    filtered = filtered.filter((event) => {
      const eventDate = new Date(event.date);
      return eventDate >= startDate;
    });

    // Filter by search query
    if (query.trim()) {
      filtered = filtered.filter((event) =>
        event.title.toLowerCase().includes(query.toLowerCase()) ||
        event.status.toLowerCase().includes(query.toLowerCase())
      );
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
            placeholder="Tìm kiếm sự kiện..."
            value={searchQuery}
            onChange={handleSearchChange}
          />
          <Search size={20} className={styles.searchIcon} />
        </div>

        {/* 2. Bộ lọc theo ngày */}
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
                  onClick={() => handleFilterChange(filter)}
                >
                  {filter}
                </button>
              ))}
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
