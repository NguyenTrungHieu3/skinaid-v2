import React from "react";
// Import type từ file DUMMY_DATA
import type { SelectedEvent } from "../../DUMMY_DATA";

// (Bạn sẽ style file này sau)
const styles = {
  card: {
    padding: "2rem",
    background: "#fff",
    borderRadius: "12px",
    border: "1px solid #e5e7eb",
  },
  noSelection: {
    textAlign: "center" as "center",
    color: "#6b7280",
  },
  image: {
    width: "100%",
    borderRadius: "8px",
    marginTop: "1rem",
  },
};

interface DetailProps {
  selectedEvent: SelectedEvent;
}

const DetailedTimelineCard = ({ selectedEvent }: DetailProps) => {
  if (!selectedEvent) {
    return (
      <div style={styles.card}>
        <div style={styles.noSelection}>
          <p>Select an analysis from the timeline to view details.</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.card}>
      <h2>{selectedEvent.title}</h2>
      <p>Status: {selectedEvent.status}</p>
      <img
        src={selectedEvent.imageUrl}
        alt={selectedEvent.title}
        style={styles.image}
      />
      {/* Hiển thị chi tiết (nếu có) */}
      {selectedEvent.detail && (
        <pre>{JSON.stringify(selectedEvent.detail, null, 2)}</pre>
      )}
      {/* Hiển thị lỗi (nếu có) */}
      {selectedEvent.error && (
        <p style={{ color: "red" }}>{selectedEvent.error}</p>
      )}
    </div>
  );
};

export default DetailedTimelineCard;
