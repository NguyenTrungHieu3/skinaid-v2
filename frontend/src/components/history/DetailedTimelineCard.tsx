// Import type từ file DUMMY_DATA
import type { CombinedEventDetail } from "../../DUMMY_DATA";

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
  selectedEvent: CombinedEventDetail | null;
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
    </div>
  );
};

export default DetailedTimelineCard;
