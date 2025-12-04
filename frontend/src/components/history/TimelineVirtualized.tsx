import { useEffect, useRef, useState } from "react";
import styles from "./Timeline.module.css";


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
}

const TimelineVirtualized = ({ events, activeEventId, onSelectEvent }: Props) => {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [currentMonth, setCurrentMonth] = useState<string>("");

  // Tính tháng khi scroll
  const handleScroll = () => {
    if (!scrollRef.current) return;

    const children = scrollRef.current.children;
    let month = currentMonth;

    for (let i = 0; i < children.length; i++) {
      const el = children[i] as HTMLElement;
      const rect = el.getBoundingClientRect();
      const center = window.innerHeight * 0.4;

      if (rect.top < center && rect.bottom > center) {
        const event = events[i];
        month = new Date(event.date).toLocaleString("en-US", {
          month: "long",
          year: "numeric",
        });
        break;
      }
    }

    setCurrentMonth(month);
  };

  useEffect(() => {
    handleScroll();
  }, [events]);

  return (
    <div className={styles.timelineContainer}>
      {/* --- FIXED MONTH LABEL (LEFT COLUMN) --- */}
      <div className={styles.monthLabelContainer}>
        <div className={styles.monthLabel}>
          {currentMonth || "Timeline"}
        </div>
      </div>

      {/* --- SCROLL LIST (RIGHT COLUMN) --- */}
      <div className={styles.eventList}>
        <div className={styles.fadeWrapper}>
          <div
            className={styles.scrollWrapper}
            ref={scrollRef}
            onScroll={handleScroll}
          >
            {events.length === 0 ? (
              <div className={styles.emptyState}>No events found</div>
            ) : (
              events.map((ev) => {
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
                          <h4 className={styles.cardTitle}>{ev.title}</h4>
                        </div>

                        <div className={styles.cardAction}>
                          <a>View</a>
                        </div>
                        
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TimelineVirtualized;
