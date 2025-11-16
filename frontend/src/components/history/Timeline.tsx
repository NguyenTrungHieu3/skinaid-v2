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

  // Tìm và nhóm các events theo tháng
  // (Phần này giữ nguyên, chỉ đảm bảo .eventList render đúng)

  return (
    <div className={styles.timelineContainer}>
      {/* CỘT 1: Nhãn Tháng (bên trái) */}
      <div className={styles.monthLabelContainer}>
        <div className={styles.monthLabel}>{monthLabel}</div>
      </div>

      {/* CỘT 2: Đường kẻ dọc */}
      {/* (Phần này đã được chuyển vào .eventList::before trong CSS) */}

      {/* CỘT 3: Danh sách các item (bên phải) */}
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
    </div>
  );
};

export default Timeline;
