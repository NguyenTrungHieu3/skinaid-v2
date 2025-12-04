import React from "react";
import styles from "./Timeline.module.css";

// --- 1. ĐỊNH NGHĨA KIỂU DỮ LIỆU ---
export interface HistoryEvent {
  id: string;
  title: string;
  date: string; // ISO date string
  status: string;
  imageUrl: string; // <-- Chúng ta sẽ dùng trường này
}

// --- 3. COMPONENT ITEM CON (Chấm tròn + Thẻ Card) ---
interface TimelineItemProps {
  event: HistoryEvent;
  isActive: boolean;
  onSelect: () => void;
}

const TimelineItem = ({ event, isActive, onSelect }: TimelineItemProps) => {
  const handleSelect = (e: React.MouseEvent) => {
    e.preventDefault();
    onSelect();
  };

  // --- SỬA LỖI Ở ĐÂY ---
  // Chúng ta không cần 'labelColorIndex' nữa

  return (
    <div
      className={`${styles.timelineItem} ${isActive ? styles.activeItem : ""}`}
    >
      {/* Chấm tròn (Đính trên đường kẻ) */}
      <div className={styles.timelineDot}></div>

      {/* Thẻ Card (Nội dung) */}
      <div className={styles.timelineCard}>
        {/* Cột 1: Thay <div> bằng <img> */}
        <img
          src={event.imageUrl} // <-- Dùng imageUrl từ props
          alt={event.title}
          className={styles.cardImage} // <-- Dùng class mới (xem CSS)
          onError={(e) => {
            // Dự phòng nếu ảnh của bạn bị lỗi
            (e.target as HTMLImageElement).src =
              "https://placehold.co/60x60/f0f0f0/b0bec5?text=Img";
          }}
        />

        {/* Cột 2: Thông tin (Timestamp và Title) */}
        <div className={styles.cardInfo}>
          <p className={styles.cardTimestamp}>
            {new Date(event.date).toLocaleString("vi-VN", {
              year: "numeric",
              month: "2-digit",
              day: "2-digit",
              hour: "2-digit",
              minute: "2-digit",
              hour12: true,
            })}
          </p>
          <h4 className={styles.cardTitle}>
            {event.title} ({event.status})
          </h4>
        </div>

        {/* Cột 3: Nút "View" */}
        <div className={styles.cardAction}>
          <a href="#" onClick={handleSelect}>
            View
          </a>
        </div>
      </div>
    </div>
  );
};

// --- 4. COMPONENT TIMELINE CHÍNH (Đường kẻ + List) ---
interface TimelineProps {
  events: HistoryEvent[];
  activeEventId: string | null;
  onSelectEvent: (id: string | null) => void;
}

const getMonthYearLabel = (events: HistoryEvent[]) => {
  if (events.length === 0) {
    return "Không có dữ liệu";
  }
  const firstEventDate = new Date(events[0].date);
  const month = firstEventDate.toLocaleString("vi-VN", { month: "numeric" });
  const year = firstEventDate.toLocaleString("vi-VN", { year: "numeric" });
  return `Tháng ${month} năm ${year}`;
};

const Timeline = ({
  events = [],
  activeEventId,
  onSelectEvent,
}: TimelineProps) => {
  const monthLabel = getMonthYearLabel(events);
  const hasEvents = events.length > 0;

  // Tìm và nhóm các events theo tháng
  // (Phần này giữ nguyên, chỉ đảm bảo .eventList render đúng)

  return (
    <div className={styles.timelineContainer}>
      {/* CỘT 1: Nhãn Tháng (bên trái) */}
      <div className={styles.monthLabelContainer}>
        {/* Chỉ hiện nhãn tháng nếu có sự kiện, nếu không thì để trống hoặc hiện text khác */}
        <div className={styles.monthLabel}>{hasEvents ? monthLabel : ""}</div>
      </div>

      {/* CỘT 2: Nội dung (Logic Rẽ Nhánh) */}
      {hasEvents ? (
        /* TRƯỜNG HỢP CÓ DỮ LIỆU -> Hiện danh sách và đường kẻ */
        <div className={styles.eventList}>
          <div className={styles.fadeWrapper}>
            <div className={styles.scrollWrapper}>
              {events.map((event) => (
                <TimelineItem
                  key={event.id}
                  event={event}
                  isActive={activeEventId === event.id}
                  onSelect={() => onSelectEvent(event.id)}
                />
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* TRƯỜNG HỢP KHÔNG CÓ DỮ LIỆU -> Hiện Empty State */
        <div className={styles.emptyStateContainer}>
          <div className={styles.emptyIconWrapper}>
            {/* Bạn có thể dùng thẻ <img /> hoặc Icon từ thư viện */}
            {/* Ví dụ dùng SVG trực tiếp: */}
            <svg
              width="40"
              height="40"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className={styles.emptyIcon}
            >
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
              <line x1="10" y1="16" x2="14" y2="12"></line>
              <line x1="10" y1="12" x2="14" y2="16"></line>
            </svg>
          </div>
          <h3 className={styles.emptyTitle}>Chưa có lịch sử</h3>
          <p className={styles.emptyDescription}>
            Bạn chưa có sự kiện phân tích nào. Hãy tải ảnh lên để bắt đầu.
          </p>
        </div>
      )}
    </div>
  );
};

export default Timeline;
