import { useState, useEffect } from "react";
import styles from "./HistoryPage.module.css";
import Timeline, { type HistoryEvent } from "../components/history/Timeline";
import HistorySidebar from "../components/history/HistorySidebar";
import HistoryDetail from "../components/history/HistoryDetail";
import { useTranslation } from "react-i18next";

// Kiểu
import { type CombinedEventDetail } from "../DUMMY_DATA";

// Service
import {
  getHistory,
  getAnalysisDetail,
  transformApiHistoryToTimeline,
  transformApiDetailToCombinedEvent,
} from "../services/historyService";

import { useAuth } from "../contexts/AuthContext";
import { Link } from "react-router-dom";

const HistoryPage = () => {
  const { t } = useTranslation();

  const { user, isAuthenticated } = useAuth();

  const [activeEventId, setActiveEventId] = useState<string | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<HistoryEvent[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<HistoryEvent[]>([]);
  const [selectedEventData, setSelectedEventData] =
    useState<CombinedEventDetail | null>(null);

  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch timeline
  useEffect(() => {
    if (!isAuthenticated) {
      setIsLoadingList(false);
      setTimelineEvents([]);
      return;
    }

    const fetchHistory = async () => {
      try {
        setIsLoadingList(true);
        setError(null);

        const apiHistoryData = await getHistory(20, 0);
        const eventsList = apiHistoryData.events || [];

        const transformed = transformApiHistoryToTimeline(eventsList);

        setTimelineEvents(transformed);
        setFilteredEvents(transformed);
      } catch (err: any) {
        setError(t("history.error.load"));
      } finally {
        setIsLoadingList(false);
      }
    };

    fetchHistory();
  }, [isAuthenticated, t]);

  // Fetch detail
  useEffect(() => {
    if (!activeEventId || !isAuthenticated) {
      setSelectedEventData(null);
      return;
    }

    const fetchDetail = async () => {
      try {
        setIsLoadingDetail(true);
        setError(null);

        const apiDetail = await getAnalysisDetail(activeEventId);
        const transform = transformApiDetailToCombinedEvent(apiDetail);

        setSelectedEventData(transform);
      } catch (err: any) {
        setError(t("history.error.load"));
      } finally {
        setIsLoadingDetail(false);
      }
    };

    fetchDetail();
  }, [activeEventId, isAuthenticated, t]);

  return (
    <div className={styles.historyPage}>
      <title>
        {t("history.title", {
          fullname: user?.full_name || user?.user_name || "",
        })}
      </title>

      {!isAuthenticated ? (
        <p className={styles.centerMsg}>{t("history.auth.not_logged_in")}</p>
      ) : (
        <main className={styles.historyContent}>
          {/* TIMELINE */}
          <div className={styles.timelineSection}>
            {isLoadingList ? (
              // Bạn có thể thay loading text bằng Spinner component nếu có
              <div className={styles.emptyContainer}>
                <p>{t("history.loading.timeline")}</p>
              </div>
            ) : error ? (
              <div className={styles.emptyContainer}>
                <p style={{ color: "red" }}>{t("history.error.load")}</p>
              </div>
            ) : filteredEvents.length === 0 ? (
              /* --- BẮT ĐẦU PHẦN EMPTY STATE MỚI --- */
              <div className={styles.emptyContainer}>
                <div className={styles.emptyIconWrapper}>
                  {/* SVG Icon: Đồng hồ/Lịch sử trống */}
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    className={styles.emptyIcon}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>

                <h3 className={styles.emptyTitle}>
                  {t("history.empty.title", "Chưa có lịch sử")}
                </h3>

                <p className={styles.emptyDescription}>
                  {t(
                    "history.empty.desc",
                    "Bạn chưa thực hiện phân tích nào. Hãy tải lên ảnh vết thương để bắt đầu theo dõi."
                  )}
                </p>

                {/* Nút điều hướng sang trang Upload (Tùy chọn) */}
                <Link to="/upload" className={styles.emptyButton}>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                    <line x1="12" y1="8" x2="12" y2="16" />
                    <line x1="8" y1="12" x2="16" y2="12" />
                  </svg>
                  {t("history.empty.button", "Tạo phân tích mới")}
                </Link>
              </div>
            ) : (
              /* --- KẾT THÚC PHẦN EMPTY STATE MỚI --- */

              <Timeline
                events={filteredEvents}
                activeEventId={activeEventId}
                onSelectEvent={setActiveEventId}
              />
            )}
          </div>

          {/* SIDEBAR / DETAILS */}
          <aside className={styles.asideSection}>
            {activeEventId ? (
              isLoadingDetail ? (
                <p>{t("history.loading.detail")}</p>
              ) : selectedEventData ? (
                <HistoryDetail
                  event={selectedEventData}
                  onClose={() => setActiveEventId(null)}
                />
              ) : (
                <p>{t("history.empty.detail")}</p>
              )
            ) : (
              <HistorySidebar
                events={timelineEvents}
                onSearchFilter={setFilteredEvents}
              />
            )}
          </aside>
        </main>
      )}
    </div>
  );
};

export default HistoryPage;
