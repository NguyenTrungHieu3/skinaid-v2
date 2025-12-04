import { useState, useEffect } from "react";
import styles from "./HistoryPage.module.css";
import TimelineVirtualized, { type HistoryEvent } from "../components/history/TimelineVirtualized";
import HistorySidebar from "../components/history/HistorySidebar";
import HistoryDetail from "../components/history/HistoryDetail";

import { type CombinedEventDetail } from "../DUMMY_DATA";
import {
  getHistory,
  getAnalysisDetail,
  deleteAnalysis,
  transformApiHistoryToTimeline,
  transformApiDetailToCombinedEvent,
} from "../services/historyService";

import { useAuth } from "../contexts/AuthContext";

const HistoryPage = () => {
  const { isAuthenticated } = useAuth();

  const [activeEventId, setActiveEventId] = useState<string | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<HistoryEvent[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<HistoryEvent[]>([]);
  const [selectedEventData, setSelectedEventData] = useState<CombinedEventDetail | null>(null);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // EFFECT 1: fetch timeline
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
        const transformedEvents = transformApiHistoryToTimeline(eventsList);

        setTimelineEvents(transformedEvents);
        setFilteredEvents(transformedEvents);
      } catch (err: any) {
        setError(err.message || "Không thể tải lịch sử.");
      } finally {
        setIsLoadingList(false);
      }
    };

    fetchHistory();
  }, [isAuthenticated]);

  // EFFECT 2: fetch detail
  useEffect(() => {
    if (!activeEventId || !isAuthenticated) {
      setSelectedEventData(null);
      return;
    }

    const fetchDetail = async () => {
      try {
        setIsLoadingDetail(true);
        setError(null);

        const apiDetailData = await getAnalysisDetail(activeEventId);
        const transformedDetail = transformApiDetailToCombinedEvent(apiDetailData);
        setSelectedEventData(transformedDetail);
      } catch (err: any) {
        setError(err.message || "Không thể tải chi tiết.");
      } finally {
        setIsLoadingDetail(false);
      }
    };

    fetchDetail();
  }, [activeEventId, isAuthenticated]);

  const handleCloseDetail = () => setActiveEventId(null);

  const handleDeleteAnalysis = async (analysisId: string) => {
    try {
      await deleteAnalysis(analysisId);

      // Remove from timeline events
      setTimelineEvents((prevEvents) =>
        prevEvents.filter((event) => event.id !== analysisId)
      );

      // Remove from filtered events
      setFilteredEvents((prevEvents) =>
        prevEvents.filter((event) => event.id !== analysisId)
      );

      // Close detail panel
      setActiveEventId(null);
      setSelectedEventData(null);
    } catch (error: any) {
      throw error;
    }
  };

  const renderSidebarContent = () => {
    if (activeEventId) {
      if (isLoadingDetail) return <p>Đang tải chi tiết...</p>;
      if (selectedEventData)
        return (
          <HistoryDetail
            event={selectedEventData}
            onClose={handleCloseDetail}
            onDelete={handleDeleteAnalysis}
          />
        );
    }
    return <HistorySidebar events={timelineEvents} onSearchFilter={setFilteredEvents} />;
  };

  return (
    <div className={styles.historyPage}>
      <main className={styles.historyContent}>
        <div className={styles.timelineSection}>
          {isLoadingList ? (
            <p>Đang tải timeline...</p>
          ) : error && filteredEvents.length === 0 ? (
            <p>Lỗi: {error}</p>
          ) : (
            <TimelineVirtualized
              events={filteredEvents}
              activeEventId={activeEventId}
              onSelectEvent={setActiveEventId}
            />
          )}
        </div>
        <aside className={styles.asideSection}>{renderSidebarContent()}</aside>
      </main>
    </div>
  );
};

export default HistoryPage;
