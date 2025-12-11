import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./Timeline.module.css";
import { useTranslation } from "react-i18next";
import i18n from "i18next";

export interface HistoryEvent {
  id: string;
  title: string;
  date: string; // ISO string
  status: string;
  imageUrl: string;
}

interface Props {
  events: HistoryEvent[];
  activeEventId: string | null;
  onSelectEvent: (id: string) => void;
  isLoading?: boolean; // <--- 1. Thêm prop này
  hasHistory: boolean; // <--- 1. THÊM PROP NÀY
}

const TimelineVirtualized = ({
  events,
  activeEventId,
  onSelectEvent,
  isLoading = false, // <--- Default value
  hasHistory,
}: Props) => {
  const navigate = useNavigate();
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [currentMonth, setCurrentMonth] = useState<string>("");
  const { t } = useTranslation();

  // --- LOGIC SCROLL (Tính tháng khi cuộn) ---
  const getLocale = () => {
    return i18n.language === "vi" ? "vi-VN" : "en-US";
  };

  const handleScroll = () => {
    if (!scrollRef.current) return;

    const children = scrollRef.current.children;
    let month = currentMonth;

    for (let i = 0; i < children.length; i++) {
      const el = children[i] as HTMLElement;
      const rect = el.getBoundingClientRect();
      // Lấy tâm màn hình để check xem item nào đang active
      const center = window.innerHeight * 0.4;

      if (rect.top < center && rect.bottom > center) {
        const event = events[i];
        if (event) {
          month = new Date(event.date).toLocaleString(getLocale(), {
            month: "long",
            year: "numeric",
          });
        }
        break;
      }
    }
    // Chỉ update nếu đang không có activeEvent (để tránh xung đột khi vừa click vừa scroll nhẹ)
    // Hoặc bạn có thể cho phép scroll override luôn. Ở đây tôi để scroll luôn cập nhật.
    setCurrentMonth(month);
  };

  // --- NHIỆM VỤ 1: Cập nhật tháng khi Click vào Item ---
  useEffect(() => {
    if (activeEventId && events.length > 0) {
      // Khi đang chọn item: Set tháng theo item đó
      const selectedEvent = events.find((e) => e.id === activeEventId);
      if (selectedEvent) {
        const monthStr = new Date(selectedEvent.date).toLocaleString(getLocale(), {
          month: "long",
          year: "numeric",
        });
        setCurrentMonth(monthStr);
      }
    } else {
      // MỚI THÊM: Khi quay lại (activeEventId = null) -> Reset về rỗng để hiện "Timeline"
      setCurrentMonth("");
      // Hoặc nếu muốn reset về tháng của item đang ở giữa màn hình scroll thì gọi lại handleScroll()
      // handleScroll();
    }
  }, [activeEventId, events, i18n.language]);

  // --- Render Empty State ---
  // --- 3. SỬA LOGIC EMPTY STATE ---
  if (!isLoading && (!events || events.length === 0)) {
    return (
      <div className={styles.scrollWrapper}>
        <div className={styles.emptyStateWrapper}>
          {/* Đổi câu thông báo tùy theo ngữ cảnh */}
          <div className={styles.emptyTitle}>
            {hasHistory
              ? t("Không tìm thấy kết quả") // Hoặc key i18n: "history.empty.search"
              : t("history.empty.history")}
          </div>

          <div className={styles.emptySubtitle}>
            {hasHistory
              ? t("Vui lòng thử từ khóa hoặc bộ lọc khác")
              : t("history.empty.detail")}
          </div>

          {/* Chỉ hiện nút Upload khi KHÔNG CÓ lịch sử (hasHistory = false) */}
          {!hasHistory && (
            <button 
              className={styles.uploadButton}
              onClick={() => navigate("/upload")}
            >
              {t("history.upload_button")}
            </button>
          )}
        </div>
      </div>
    );
  }
  // --- 2. LOGIC RENDER SKELETON ---
  // Tạo một mảng giả gồm 5 phần tử để hiển thị khi loading
  const renderSkeletons = () => {
    return Array.from({ length: 5 }).map((_, index) => (
      <div key={`skeleton-${index}`} className={styles.eventScrollWrapper}>
        <div className={styles.timelineItem}>
          {/* Dot giả */}
          <div className={`${styles.timelineDot} ${styles.skeletonDot}`} />

          {/* Card giả */}
          <div className={`${styles.timelineCard} ${styles.skeletonCard}`}>
            {/* Ảnh lấp lánh */}
            <div className={`${styles.skeletonImage} ${styles.skeletonAnim}`} />

            {/* Nội dung lấp lánh */}
            <div className={styles.skeletonContent}>
              {/* Dòng ngày tháng (ngắn) */}
              <div
                className={`${styles.skeletonLine} ${styles.skeletonAnim}`}
                style={{ width: "30%" }}
              />
              {/* Dòng tiêu đề (dài hơn) */}
              <div
                className={`${styles.skeletonLine} ${styles.skeletonAnim}`}
                style={{ width: "70%", height: "16px" }}
              />
            </div>

            {/* Nút View giả */}
            <div
              className={`${styles.skeletonAction} ${styles.skeletonAnim}`}
            />
          </div>
        </div>
      </div>
    ));
  };

  // --- 3. CHECK EMPTY STATE (Cập nhật logic) ---
  // Nếu không loading VÀ không có events thì mới hiện Empty State
  // --- 3. SỬA LOGIC EMPTY STATE ---
  if (!isLoading && (!events || events.length === 0)) {
    return (
      <div className={styles.scrollWrapper}>
        <div className={styles.emptyStateWrapper}>
          {/* SỬA 1: Đổi tiêu đề tùy theo ngữ cảnh */}
          <div className={styles.emptyTitle}>
            {
              hasHistory
                ? t("Không tìm thấy kết quả") // Khi có lịch sử nhưng search không ra
                : t("history.empty.history") // Khi chưa có lịch sử nào
            }
          </div>

          {/* SỬA 2: Đổi phụ đề */}
          <div className={styles.emptySubtitle}>
            {hasHistory
              ? t("Vui lòng thử từ khóa hoặc bộ lọc khác")
              : t("history.empty.detail")}
          </div>

          {/* SỬA 3: Chỉ hiện nút Upload khi KHÔNG CÓ lịch sử (hasHistory = false) */}
          {!hasHistory && (
            <button 
              className={styles.uploadButton}
              onClick={() => navigate("/upload")}
            >
              {t("history.upload_button")}
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={styles.timelineContainer}>
      {/* CỘT TRÁI: THÁNG */}
      <div className={styles.monthLabelContainer}>
        <div className={styles.monthLabel}>{currentMonth || "Timeline"}</div>
      </div>

      {/* CỘT PHẢI: LIST */}
      <div className={styles.eventList}>
        {/* --- NHIỆM VỤ 2: Đường kẻ thẳng full chiều cao (Nằm dưới list) --- */}
        <div className={styles.continuousLine}></div>

        <div className={styles.fadeWrapper}>
          <div
            className={styles.scrollWrapper}
            ref={scrollRef}
            onScroll={handleScroll}
          >
            {/* --- 4. RENDER LOGIC --- */}
            {isLoading
              ? renderSkeletons() // Render khung xương khi load
              : events.map((ev) => {
                  const isActive = ev.id === activeEventId;

                  return (
                    <div key={ev.id} className={styles.eventScrollWrapper}>
                      <div className={styles.timelineItem}>
                        {/* DOT */}
                        <div
                          className={`${styles.timelineDot} ${
                            isActive ? styles.activeDot : ""
                          }`}
                        />

                        {/* CARD */}
                        <div
                          className={`${styles.timelineCard} ${
                            isActive ? styles.activeItem : ""
                          }`}
                          onClick={() => onSelectEvent(ev.id)}
                        >
                          <img
                            src={ev.imageUrl}
                            alt=""
                            className={styles.cardImage}
                          />
                          <div className={styles.cardInfo}>
                            <p className={styles.cardTimestamp}>
                              {new Date(ev.date).toLocaleString("en-US", {
                                hour: "2-digit",
                                minute: "2-digit",
                                day: "2-digit",
                                month: "short",
                              })}
                            </p>
                            <h4 className={styles.cardTitle}>{t("history.analysis")} {ev.title}</h4>
                          </div>
                          <div className={styles.cardAction}>
                            <a>{t("history.view")}</a>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TimelineVirtualized;
