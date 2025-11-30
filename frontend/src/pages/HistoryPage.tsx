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
              <p>{t("history.loading.timeline")}</p>
            ) : error ? (
              <p>{t("history.error.load")}</p>
            ) : filteredEvents.length === 0 ? (
              <p>{t("history.empty.history")}</p>
            ) : (
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
