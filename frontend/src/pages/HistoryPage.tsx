import { useState, useEffect } from "react";
import styles from "./HistoryPage.module.css";
import TimelineVirtualized, {
  type HistoryEvent,
} from "../components/history/TimelineVirtualized";
import HistorySidebar from "../components/history/HistorySidebar";
import HistoryDetail from "../components/history/HistoryDetail";

import { type CombinedEventDetail } from "../types/appTypes";
import {
  getHistory,
  getAnalysisDetail,
  deleteAnalysis,
  transformApiHistoryToTimeline,
  transformApiDetailToCombinedEvent,
} from "../services/historyService";

import { useAuth } from "../contexts/AuthContext";
import { useTranslation } from "react-i18next";

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
        const transformedDetail =
          transformApiDetailToCombinedEvent(apiDetailData);
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
      if (isLoadingDetail) return <p>{t("history.loading.details")}</p>;
      if (selectedEventData)
        return (
          <HistoryDetail
            event={selectedEventData}
            onClose={handleCloseDetail}
            onDelete={handleDeleteAnalysis}
          />
        );
    }
    return (
      <HistorySidebar
        events={timelineEvents}
        onSearchFilter={setFilteredEvents}
      />
    );
  };

  // 1. Kiểm tra xem người dùng CÓ dữ liệu gốc hay không (chứ không phải dữ liệu đã lọc)
  const hasHistoryData = timelineEvents.length > 0;

  // 2. Sidebar hiện khi:
  // - Không đang loading
  // - Không lỗi
  // - VÀ có dữ liệu gốc (hasHistoryData)
  //   (Dù search ra 0 kết quả thì vẫn hiện sidebar để người dùng còn xóa từ khóa search)
  const showSidebar = !isLoadingList && !error && hasHistoryData;

  return (
    <div className={styles.historyPage}>
      <title>
        {t("title.history_page", {
          fullname: user?.full_name || user?.user_name,
        })}
      </title>

      <main className={styles.historyContent}>
        {/* THÊM LOGIC CLASS: 
            Nếu không hiện sidebar, timelineSection cần bỏ giới hạn max-width 
            để Empty State hiển thị ra giữa màn hình.
        */}
        <div
          className={`${styles.timelineSection} ${
            !showSidebar ? styles.fullWidth : ""
          }`}
        >
          {isLoadingList ? (
            <p style={{ color: "#00897b" }}>{t("history.loading.timeline")}</p>
          ) : error ? (
            // SỬA TẠI ĐÂY: In thẳng lỗi ra màn hình & Console để debug
            <div style={{ textAlign: "center", color: "red" }}>
              <p>Có lỗi xảy ra: {error}</p>
              <p>Key i18n: {t("error.detail", { error: error })}</p>
            </div>
          ) : (
            <TimelineVirtualized
              events={filteredEvents}
              activeEventId={activeEventId}
              onSelectEvent={setActiveEventId}
              isLoading={isLoadingList} // <--- Truyền state loading vào đây
              hasHistory={timelineEvents.length > 0}
            />
          )}
        </div>

        {/* LOGIC ẨN SIDEBAR:
            Chỉ render aside khi showSidebar = true
        */}
        {showSidebar && (
          <aside className={styles.asideSection}>
            {renderSidebarContent()}
          </aside>
        )}
      </main>
    </div>
  );
};

export default HistoryPage;
