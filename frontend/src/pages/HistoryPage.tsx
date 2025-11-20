import React, { useState, useEffect } from "react";
import styles from "./HistoryPage.module.css";
import Timeline, { type HistoryEvent } from "../components/history/Timeline";
import HistorySidebar from "../components/history/HistorySidebar";
import HistoryDetail from "../components/history/HistoryDetail";

// Import kiểu frontend
import { type CombinedEventDetail } from "../DUMMY_DATA";

// Import service
import {
  getHistory,
  getAnalysisDetail,
  transformApiHistoryToTimeline,
  transformApiDetailToCombinedEvent,
} from "../services/historyService";

// Import 'useAuth' để kiểm tra đăng nhập
import { useAuth } from "../contexts/AuthContext";

const HistoryPage = () => {
  const { isAuthenticated } = useAuth(); // Lấy trạng thái đăng nhập

  const [activeEventId, setActiveEventId] = useState<string | null>(null);

  const [timelineEvents, setTimelineEvents] = useState<HistoryEvent[]>([]);
  const [selectedEventData, setSelectedEventData] =
    useState<CombinedEventDetail | null>(null);

  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // EFFECT 1: Tải danh sách Timeline (CÓ DELAY 1 GIÂY)
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

        // --- 🔥 CẬP NHẬT: Dùng Promise.all để delay ít nhất 1 giây 🔥 ---
        const [apiHistoryData] = await Promise.all([
          getHistory(20, 0), // Gọi API
          new Promise((resolve) => setTimeout(resolve, 500)), // Delay 1s
        ]);

        const eventsList = apiHistoryData.events || [];
        const transformedEvents = transformApiHistoryToTimeline(eventsList);

        setTimelineEvents(transformedEvents);
      } catch (err: any) {
        setError(err.message || "Không thể tải lịch sử.");
      } finally {
        setIsLoadingList(false);
      }
    };

    fetchHistory();
  }, [isAuthenticated]);

  // EFFECT 2: Tải chi tiết (CÓ DELAY 1 GIÂY)
  useEffect(() => {
    if (!activeEventId || !isAuthenticated) {
      setSelectedEventData(null);
      return;
    }

    const fetchDetail = async () => {
      try {
        setIsLoadingDetail(true); // Bắt đầu loading
        setError(null);

        // Sử dụng Promise.all để chạy song song:
        const [apiDetailData] = await Promise.all([
          getAnalysisDetail(activeEventId),
          new Promise((resolve) => setTimeout(resolve, 250)), // Delay giả 1s
        ]);

        const transformedDetail =
          transformApiDetailToCombinedEvent(apiDetailData);
        setSelectedEventData(transformedDetail);
      } catch (err: any) {
        setError(err.message || "Không thể tải chi tiết.");
      } finally {
        setIsLoadingDetail(false); // Tắt loading sau khi đã đợi đủ 1s và có dữ liệu
      }
    };

    fetchDetail();
  }, [activeEventId, isAuthenticated]);

  const handleCloseDetail = () => {
    setActiveEventId(null);
  };

  // Hàm render nội dung bên phải
  const renderSidebarContent = () => {
    // Trường hợp 1: Đang loading chi tiết
    if (activeEventId && isLoadingDetail) {
      return (
        <div className={styles.asideSection}>
          <div className={styles.loadingContainer}>
            <div className={styles.spinner}></div>
            <span className={styles.loadingText}>Đang tải chi tiết...</span>
          </div>
        </div>
      );
    }

    // Trường hợp 2: Đã có dữ liệu chi tiết
    if (activeEventId && selectedEventData) {
      return (
        <div className={styles.asideSection}>
          <HistoryDetail
            event={selectedEventData}
            onClose={handleCloseDetail}
          />
        </div>
      );
    }

    // Trường hợp 3: Mặc định (Sidebar lịch sử chung/Thống kê)
    return (
      <div className={styles.asideSection}>
        <HistorySidebar />
      </div>
    );
  };

  return (
    <div className={styles.historyPage}>
      <main className={styles.historyContent}>
        {/* CỘT 1: PHẦN TIMELINE */}
        <div className={styles.timelineSection}>
          {isLoadingList ? (
            // --- Render Skeleton khi đang tải ---
            <div className={styles.skeletonWrapper}>
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className={styles.skeletonItem}>
                  <div className={styles.skeletonMarker}></div>
                  <div className={styles.skeletonContent}>
                    <div className={styles.skeletonTitle}></div>
                    <div className={styles.skeletonBody}></div>
                  </div>
                </div>
              ))}
            </div>
          ) : error && timelineEvents.length === 0 ? (
            <p style={{ padding: "20px", color: "red", textAlign: "center" }}>
              Lỗi: {error}
            </p>
          ) : (
            <Timeline
              events={timelineEvents}
              activeEventId={activeEventId}
              onSelectEvent={setActiveEventId}
            />
          )}
        </div>

        {/* CỘT 2: KHỐI NỘI DUNG */}
        {renderSidebarContent()}
      </main>
    </div>
  );
};

export default HistoryPage;
