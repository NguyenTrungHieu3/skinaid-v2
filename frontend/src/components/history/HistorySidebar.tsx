import { useState } from "react";
import styles from "./HistorySidebar.module.css";
import { Search, Filter } from "lucide-react";
import LogoPlaceholder from "../../assets/images/general/logo_placeholder.png";
import type { HistoryEvent } from "./Timeline";
import { useTranslation } from "react-i18next";

// Props
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
  const [activeFilter, setActiveFilter] = useState("7d");
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Filter options (dùng key → dịch bằng i18n)
  const filters = [
    "1_day",
    "3_days",
    "7_days",
    "1_month",
    "3_months",
    "6_months",
    "1_year",
  ];

  // Map số ngày tương ứng
  const daysToSubtract: Record<string, number> = {
    "1_day": 1,
    "3_days": 3,
    "7_days": 7,
    "1_month": 30,
    "3_months": 90,
    "6_months": 180,
    "1_year": 365,
  };

  // Filtering logic
  const filterEvents = (query: string, dateFilter: string) => {
    let filtered = events;

    // Date filter
    const now = new Date();
    const days = daysToSubtract[dateFilter] || 7;
    const startDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

    filtered = filtered.filter((event) => {
      const eventDate = new Date(event.date);
      return eventDate >= startDate;
    });

    // Search filter
    if (query.trim()) {
      filtered = filtered.filter(
        (event) =>
          event.title.toLowerCase().includes(query.toLowerCase()) ||
          event.status.toLowerCase().includes(query.toLowerCase())
      );
    }

    return filtered;
  };

  // Handle search
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    const filtered = filterEvents(query, activeFilter);
    onSearchFilter(filtered);
  };

  // Handle filter change
  const handleFilterChange = (filter: string) => {
    setActiveFilter(filter);
    const filtered = filterEvents(searchQuery, filter);
    onSearchFilter(filtered);
    setIsFilterOpen(false);
  };

  return (
    <div className={styles.sidebarContainer}>
      <div className={styles.topControlsWrapper}>
        {/* Search bar */}
        <div className={styles.searchBar}>
          <input
            type="text"
            placeholder={t("history.search_placeholder")}
            value={searchQuery}
            onChange={handleSearchChange}
          />
          <Search size={20} className={styles.searchIcon} />
        </div>

        {/* Filters */}
        <div className={styles.filterSection}>
          <div className={styles.filterHeader}>
            <span>{t("history.filter_label")}</span>
            <Filter
              size={15}
              className={styles.filterIcon}
              onClick={() => setIsFilterOpen((prev) => !prev)}
            />
          </div>

          {isFilterOpen && (
            <div className={styles.filterOptions}>
              {filters.map((filterKey) => (
                <button
                  key={filterKey}
                  className={`${styles.filterButton} ${
                    activeFilter === filterKey ? styles.activeFilter : ""
                  }`}
                  onClick={() => handleFilterChange(filterKey)}
                >
                  {t(`history.date_filters.${filterKey}`)}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Logo */}
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
