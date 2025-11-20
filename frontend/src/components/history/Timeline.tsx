import React, { useState, useEffect, useRef } from "react";
import styles from "./Timeline.module.css";

// --- 1. ĐỊNH NGHĨA KIỂU DỮ LIỆU ---
export interface HistoryEvent {
  id: string;
  title: string;
  date: string; // ISO date string
  status: string;
  imageUrl: string;
}

// --- 2. VISUAL STATE TYPE ---
interface VisualState {
  opacity: number;
  scale: number;
  translateX: number;
  blur: number;
  zIndex: number;
}

// --- 3. COMPONENT ITEM CON ---
interface TimelineItemProps {
  event: HistoryEvent;
  isActive: boolean;
  onSelect: () => void;
  state: VisualState;
}

const TimelineItem = ({ event, isActive, onSelect, state }: TimelineItemProps) => {
  const handleSelect = (e: React.MouseEvent) => {
    e.preventDefault();
    onSelect();
  };

  return (
    <div
      className={`${styles.timelineItem} ${isActive ? styles.activeItem : ""}`}
      style={{
        opacity: state.opacity,
        transform: `translateX(${state.translateX}rem) scale(${state.scale})`,
        filter: `blur(${state.blur}px)`,
        zIndex: state.zIndex,
        pointerEvents: state.opacity === 0 ? 'none' : 'auto',
        transition: 'all 0.2s cubic-bezier(0.25, 0.1, 0.25, 1)'
      }}
    >
      {/* Chấm tròn */}
      <div className={`${styles.timelineDot} ${isActive ? styles.activeDot : ""}`}></div>

      {/* Thẻ Card */}
      <div className={styles.timelineCard}>
        <img
          src={event.imageUrl}
          alt={event.title}
          className={styles.cardImage}
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              "https://placehold.co/60x60/f0f0f0/b0bec5?text=Img";
          }}
        />

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
            {event.title}
          </h4>
          <h4 className={styles.cardTitle}>
            {event.status}
          </h4>
        </div>

        <div className={styles.cardAction}>
          <a href="#" onClick={handleSelect}>
            {isActive ? "Selected ✓" : "View →"}
          </a>
        </div>
      </div>
    </div>
  );
};

// --- 4. COMPONENT TIMELINE CHÍNH ---
interface TimelineProps {
  events: HistoryEvent[];
  activeEventId: string | null;
  onSelectEvent: (id: string | null) => void;
}

const getMonthYearLabel = (events: HistoryEvent[], focusedIndex: number) => {
  if (events.length === 0) {
    return "Không có dữ liệu";
  }
  const focusedEvent = events[focusedIndex];
  if (!focusedEvent) return "Không có dữ liệu";
  
  const date = new Date(focusedEvent.date);
  const month = date.toLocaleString("vi-VN", { month: "long" });
  const year = date.toLocaleString("vi-VN", { year: "numeric" });
  return `${month} ${year}`;
};

const Timeline = ({
  events = [],
  activeEventId,
  onSelectEvent,
}: TimelineProps) => {
  const [focusedIndex, setFocusedIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const eventRefs = useRef<(HTMLDivElement | null)[]>([]);

  const monthLabel = getMonthYearLabel(events, focusedIndex);

  // Get visual state for each event
  const getEventState = (index: number): VisualState => {
    const distance = Math.abs(index - focusedIndex);

    if (distance === 0) {
      return { opacity: 1, scale: 1.2, translateX: 2, blur: 0, zIndex: 10 };
    } else if (distance === 1) {
      return { opacity: 0.6, scale: 0.95, translateX: -2, blur: 1, zIndex: 5 };
    } else if (distance === 2) {
      return { opacity: 0.3, scale: 0.9, translateX: -4, blur: 2, zIndex: 3 };
    } else {
      return { opacity: 0, scale: 0.85, translateX: -6, blur: 4, zIndex: 1 };
    }
  };

  // Scroll detection
  useEffect(() => {
    const scrollWrapper = containerRef.current?.querySelector(`.${styles.scrollWrapper}`);
    if (!scrollWrapper) return;

    const handleScroll = () => {
      const containerRect = scrollWrapper.getBoundingClientRect();
      const viewportCenter = containerRect.top + containerRect.height / 2;
      let closestIndex = 0;
      let minDistance = Infinity;

      eventRefs.current.forEach((ref, index) => {
        if (ref) {
          const rect = ref.getBoundingClientRect();
          const eventCenter = rect.top + rect.height / 2;
          const distance = Math.abs(eventCenter - viewportCenter);

          if (distance < minDistance) {
            minDistance = distance;
            closestIndex = index;
          }
        }
      });

      setFocusedIndex(closestIndex);
    };

    scrollWrapper.addEventListener('scroll', handleScroll);
    handleScroll();

    return () => scrollWrapper.removeEventListener('scroll', handleScroll);
  }, [events.length]);

  // Wheel handler for smooth navigation
  const handleWheel = (e: WheelEvent) => {
    e.preventDefault();

    let nextIndex;
    if (e.deltaY > 0) {
      nextIndex = Math.min(focusedIndex + 1, events.length - 1);
    } else {
      nextIndex = Math.max(focusedIndex - 1, 0);
    }

    eventRefs.current[nextIndex]?.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    });

    setFocusedIndex(nextIndex);
  };

  useEffect(() => {
    const scrollWrapper = containerRef.current?.querySelector(`.${styles.scrollWrapper}`);
    if (!scrollWrapper) return;

    scrollWrapper.addEventListener('wheel', handleWheel as any, { passive: false });
    return () => scrollWrapper.removeEventListener('wheel', handleWheel as any);
  }, [focusedIndex, events.length]);

  // Handle event click
  const handleEventClick = (eventId: string, index: number) => {
    // Update focused index
    setFocusedIndex(index);
    
    // Scroll to event
    eventRefs.current[index]?.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    });
    
    // Toggle selection
    if (activeEventId === eventId) {
      onSelectEvent(null);
    } else {
      onSelectEvent(eventId);
    }
  };

  if (events.length === 0) {
    return (
      <div className={styles.timelineContainer}>
        <div className={styles.emptyState}>Hãy thêm ảnh nào!</div>
      </div>
    );
  }

  return (
    <div className={styles.timelineContainer} ref={containerRef}>
      {/* SVG Curved Line - Fixed */}
      <div className={styles.timelineLineFixed}>
        <svg className={styles.timelineSvg} viewBox="0 0 400 1000" preserveAspectRatio="none">
          <defs>
            <linearGradient id="fadeStroke" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00897b" stopOpacity="0" />
              <stop offset="30%" stopColor="#00897b" stopOpacity="1" />
              <stop offset="70%" stopColor="#00897b" stopOpacity="1" />
              <stop offset="100%" stopColor="#00897b" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path
            d="M50 0 C 150 0, 150 1000, 50 1000"
            stroke="url(#fadeStroke)"
            strokeWidth="4"
            fill="transparent"
          />
        </svg>
      </div>

      {/* CỘT 1: Nhãn Tháng */}
      <div className={styles.monthLabelContainer}>
        <div className={styles.monthLabel}>{monthLabel}</div>
      </div>

      {/* CỘT 2: Danh sách các item */}
      <div className={styles.eventList}>
        <div className={styles.fadeWrapper}>
          <div className={styles.scrollWrapper}>
            {events.map((event, index) => {
              const state = getEventState(index);
              
              return (
                <div
                  key={event.id}
                  ref={(el) => (eventRefs.current[index] = el)}
                  className={styles.eventScrollWrapper}
                >
                  <TimelineItem
                    event={event}
                    isActive={activeEventId === event.id}
                    onSelect={() => handleEventClick(event.id, index)}
                    state={state}
                  />
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Timeline;