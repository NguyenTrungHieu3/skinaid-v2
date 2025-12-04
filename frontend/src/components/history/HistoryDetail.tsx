import { useState } from "react";
import styles from "./HistoryDetail.module.css";
import { ArrowLeft } from "lucide-react";
import {
  type CombinedEventDetail,
  type SingleWoundDetail,
} from "../../types/appTypes"; // Nên import từ file types/appTypes.ts

interface HistoryDetailProps {
  event: CombinedEventDetail;
  onClose: () => void;
}

const HistoryDetail = ({ event, onClose }: HistoryDetailProps) => {
  const [activeIndex, setActiveIndex] = useState(0);

  const currentWound: SingleWoundDetail | null =
    event.detail[activeIndex] || null;

  const showTabs = event.detail.length > 1;

  // --- LỖI CRASH: Biến 'firstAidSteps' đã được XÓA khỏi đây ---
  // Nó sẽ được chuyển vào bên trong 'currentWound' check

  return (
    <div className={styles.detailContainer}>
      {/* 1. Header (Nút quay lại) - Không đổi */}
      <div className={styles.detailHeader}>
        <button onClick={onClose} className={styles.backButton}>
          <ArrowLeft size={20} />
          <span>Quay lại</span>
        </button>
      </div>

      {/* 2. Ảnh chính (Không đổi) */}
      <div className={styles.imageContainer}>
        <img
          src={event.imageUrl}
          alt={event.title}
          className={styles.mainImage}
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              "https://placehold.co/400x300/e0e0e0/9e9e9e?text=Image+Error";
          }}
        />
      </div>

      {/* 3. KHỐI MỚI: Các Tab (Nút chuyển đổi) - Không đổi */}
      {showTabs && (
        <div className={styles.woundTabs}>
          {event.detail.map((wound, index) => (
            <button
              key={index}
              className={`${styles.woundTab} ${
                index === activeIndex ? styles.activeTab : ""
              }`}
              onClick={() => setActiveIndex(index)}
            >
              {wound.type} (Vết {index + 1})
            </button>
          ))}
        </div>
      )}

      {/* 4. Thông tin (Giờ sẽ lấy từ currentWound) */}
      {currentWound ? (
        <>
          <div className={styles.infoSection}>
            <h3 className={styles.title}>{currentWound.type}</h3>

            {/* --- SỬA LỖI HIỂN THỊ MỨC ĐỘ --- */}
            <span
              className={`${styles.statusBadge} ${
                currentWound.severity === "Trung bình"
                  ? styles.moderate
                  : currentWound.severity === "Nặng"
                  ? styles.severe
                  : styles.mild
              }`}
            >
              {currentWound.severity} {/* <-- SỬA LỖI Ở ĐÂY: Dùng severity */}
            </span>
            {/* --- (Kết thúc sửa lỗi) --- */}

            <p className={styles.date}>
              {new Date(event.date).toLocaleString("vi-VN")}
            </p>
          </div>

          {/* 5. Chi tiết Phân tích */}
          <div className={styles.analysisSection}>
            <h4>Chi tiết Phân tích</h4>

            {/* --- SỬA LỖI CRASH: Di chuyển logic firstAidSteps vào đây --- */}
            {(() => {
              // Logic này giờ đã an toàn vì currentWound chắc chắn tồn tại
              const firstAidSteps = currentWound.firstAid
                ?.split(/\d+\.\s+/) // Tách bằng số (ví dụ: "1. ")
                .filter(Boolean) // Loại bỏ chuỗi rỗng
                .map((step) => step.trim()); // Xóa khoảng trắng thừa

              return (
                <>
                  {/* Độ chính xác (Không đổi) */}
                  <div className={styles.detailItem}>
                    <h5>Độ chính xác</h5>
                    <div className={styles.accuracyMeter}>
                      <div
                        className={styles.accuracyBar}
                        style={{ width: `${currentWound.accuracy}%` }}
                      >
                        {Math.round(currentWound.accuracy)}%
                      </div>
                    </div>
                  </div>

                  {/* Mô tả (Không đổi)
                  <div className={styles.detailItem}>
                    <h5>Mô tả</h5>
                    <p>{currentWound.description}</p>
                  </div> */}

                  {/* Gợi ý sơ cứu (Dùng biến 'firstAidSteps' đã sửa) */}
                  <div className={styles.detailItem}>
                    <h5>Gợi ý sơ cứu</h5>
                    <div className={styles.firstAidSteps}>
                      {firstAidSteps && firstAidSteps.length > 0 ? (
                        firstAidSteps.map((step, index) => (
                          <p key={index} className={styles.firstAidStep}>
                            <span>{index + 1}.</span>
                            <span>{step}</span>
                          </p>
                        ))
                      ) : (
                        // Fallback: Nếu không tách được (ví dụ: "Chườm lạnh")
                        <p>{currentWound.firstAid || "Không có gợi ý."}</p>
                      )}
                    </div>
                  </div>

                  {/* Thời gian hồi phục (Không đổi) */}
                  <div className={styles.detailItem}>
                    <h5>Thời gian hồi phục (dự kiến)</h5>
                    <p>{currentWound.healingTime}</p>
                  </div>
                </>
              );
            })()}
            {/* --- (Kết thúc sửa lỗi) --- */}
          </div>
        </>
      ) : (
        // Trường hợp không có chi tiết nào
        <div className={styles.infoSection}>
          <p>Không có chi tiết phân tích cho sự kiện này.</p>
        </div>
      )}
    </div>
  );
};

export default HistoryDetail;
