import { useState, useEffect } from "react";
import styles from "./HistoryPage.module.css";
import Timeline, { type HistoryEvent } from "../components/history/Timeline";
import HistorySidebar from "../components/history/HistorySidebar";
import HistoryDetail from "../components/history/HistoryDetail";

// Import kiểu frontend
import {
  type CombinedEventDetail,
} from "../DUMMY_DATA"; // Hoặc từ src/types/appTypes.ts

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
  const [filteredEvents, setFilteredEvents] = useState<HistoryEvent[]>([]);
  const [selectedEventData, setSelectedEventData] =
    useState<CombinedEventDetail | null>(null);

  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // EFFECT 1: Tải danh sách Timeline
  useEffect(() => {
    // Chỉ fetch nếu đã đăng nhập
    if (!isAuthenticated) {
      setIsLoadingList(false);
      setTimelineEvents([]); // Đảm bảo danh sách trống
      return;
    }

    const fetchHistory = async () => {
      try {
        setIsLoadingList(true);
        setError(null);

        const apiHistoryData = await getHistory(20, 0);

        // --- 🔥 ĐÂY LÀ PHẦN SỬA LỖI 🔥 ---
        // Thêm '|| []' để đảm bảo 'eventsList' luôn là một mảng
        // ngay cả khi 'apiHistoryData.events' là 'undefined'.
        const eventsList = apiHistoryData.events || [];
        // --- (Kết thúc sửa lỗi) ---

        const transformedEvents = transformApiHistoryToTimeline(
          eventsList // Truyền biến 'eventsList' an toàn
        );

        setTimelineEvents(transformedEvents);
        setFilteredEvents(transformedEvents); // Initialize filtered events
      } catch (err: any) {
        setError(err.message || "Không thể tải lịch sử.");
      } finally {
        setIsLoadingList(false);
      }
    };

    fetchHistory();
  }, [isAuthenticated]); // Thêm 'isAuthenticated' vào dependencies

  // EFFECT 2: Tải chi tiết
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

  const handleCloseDetail = () => {
    setActiveEventId(null);
  };

  // Hàm render cho cột bên phải (Aside)
  const renderSidebarContent = () => {
    if (activeEventId) {
      if (isLoadingDetail) {
        return <p>Đang tải chi tiết...</p>;
      }
      if (selectedEventData) {
        return (
          <HistoryDetail
            event={selectedEventData}
            onClose={handleCloseDetail}
          />
        );
      }
    }
    return (
      <HistorySidebar
        events={timelineEvents}
        onSearchFilter={setFilteredEvents}
      />
    );
  };

  return (
    <div className={styles.historyPage}>
      <main className={styles.historyContent}>
        {/* CỘT 1: PHẦN TIMELINE (Đã cập nhật) */}
        <div className={styles.timelineSection}>
          {isLoadingList ? (
            <p>Đang tải timeline...</p>
          ) : error && filteredEvents.length === 0 ? (
            <p>Lỗi: {error}</p>
          ) : (
            <Timeline
              events={filteredEvents}
              activeEventId={activeEventId}
              onSelectEvent={setActiveEventId}
            />
          )}
        </div>

        {/* CỘT 2: KHỐI NỘI DUNG (Đã cập nhật) */}
        <aside className={styles.asideSection}>{renderSidebarContent()}</aside>
      </main>
    </div>
  );
};

export default HistoryPage;