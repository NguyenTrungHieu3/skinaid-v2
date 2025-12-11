import { useState } from "react";
import styles from "./HistoryDetail.module.css";
import { ArrowLeft, Trash2 } from "lucide-react";
import {
  type CombinedEventDetail,
  type SingleWoundDetail,
} from "../../types/appTypes";

interface HistoryDetailProps {
  event: CombinedEventDetail;
  onClose: () => void;
  onDelete: (eventId: string) => Promise<void>;
}

const HistoryDetail = ({ event, onClose, onDelete }: HistoryDetailProps) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const currentWound: SingleWoundDetail | null =
    event.detail[activeIndex] || null;

  const showTabs = event.detail.length > 1;

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
    setDeleteError(null);
  };

  const handleConfirmDelete = async () => {
    try {
      setIsDeleting(true);
      setDeleteError(null);
      await onDelete(event.id);
      setShowDeleteConfirm(false);
      onClose();
    } catch (error: any) {
      setDeleteError(
        error.message || "Không thể xóa bản ghi. Vui lòng thử lại."
      );
      setIsDeleting(false);
    }
  };

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
    setDeleteError(null);
  };

  return (
    <div className={styles.detailContainer}>
      {/* 1. Header (Nút quay lại) */}
      <div className={styles.detailHeader}>
        <button onClick={onClose} className={styles.backButton}>
          <ArrowLeft size={20} />
          <span>Quay lại</span>
        </button>
        <button
          onClick={handleDeleteClick}
          disabled={isDeleting || showDeleteConfirm}
          className={styles.deleteButton}
          title="Xóa bản ghi này"
        >
          <Trash2 size={20} />
        </button>
      </div>

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className={styles.confirmDialog}>
          <div className={styles.confirmContent}>
            <h3>Xác nhận xóa</h3>
            <p>
              Bạn có chắc chắn muốn xóa bản ghi phân tích này? Hành động này
              không thể hoàn tác.
            </p>
            <div className={styles.confirmActions}>
              <button
                onClick={handleCancelDelete}
                disabled={isDeleting}
                className={styles.cancelButton}
              >
                Không, giữ lại
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className={styles.confirmButton}
              >
                {isDeleting ? "Đang xóa..." : "Có, xóa bản ghi"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Show delete error if any */}
      {deleteError && <div className={styles.errorMessage}>{deleteError}</div>}

      {currentWound && <h2>{currentWound.titleGuide}</h2>}

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
            <div className={styles.woundname}>
              <h3 className={styles.title}>{currentWound.type}</h3>

              {/* --- SỬA LỖI HIỂN THỊ MỨC ĐỘ --- */}
              <span
                className={`${styles.statusBadge} ${
                  currentWound.severity === "moderate"
                    ? styles.moderate
                    : styles.mild
                }`}
              >
                {currentWound.severity} {/* <-- SỬA LỖI Ở ĐÂY: Dùng severity */}
              </span>
              {/* --- (Kết thúc sửa lỗi) --- */}
              <span
                className={`${
                  currentWound.sub_type === "skintear" ||
                  currentWound.sub_type === "blister"
                    ? styles.moderate
                    : styles.statusBadge
                }`}
              >
                {currentWound.sub_type}
              </span>
            </div>

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
                  {/* Độ chính xác */}
                  <div className={styles.detailItem}>
                    <h5>Độ chính xác</h5>
                    <div className={styles.accuracyMeter}>
                      <div
                        // Logic xác định class màu sắc
                        className={`${styles.accuracyBar} ${
                          currentWound.accuracy < 30
                            ? styles.accLow // Dưới 30% -> Đỏ
                            : currentWound.accuracy <= 65
                            ? styles.accMedium // 30% - 65% -> Vàng
                            : styles.accHigh // Trên 65% -> Xanh
                        }`}
                        style={{ width: `${currentWound.accuracy}%` }}
                      >
                        {Math.round(currentWound.accuracy)}%
                      </div>
                    </div>
                  </div>

                  {/* Thời gian hồi phục (Không đổi) */}
                  <div className={styles.detailItem}>
                    <h5>Thời gian hồi phục (dự kiến)</h5>
                    <p>
                      <strong>{currentWound.healingTime}</strong>
                    </p>
                  </div>

                  {/* Vật tư cần thiết */}
                  <div className={styles.detailItem}>
                    <h5>Vật tư cần thiết</h5>
                    <div className={styles.firstAidSteps}>
                      {(() => {
                        const suppliesSteps = currentWound.suppliesNeeded
                          ?.split(/\d+\.\s+/)
                          .filter(Boolean)
                          .map((step) => step.trim());

                        return suppliesSteps && suppliesSteps.length > 0 ? (
                          suppliesSteps.map((step, index) => (
                            <p key={index} className={styles.firstAidStep}>
                              <span>{index + 1}</span>
                              <span>{step}</span>
                            </p>
                          ))
                        ) : (
                          <p>
                            {currentWound.suppliesNeeded ||
                              "Không có thông tin."}
                          </p>
                        );
                      })()}
                    </div>
                  </div>

                  {/* Gợi ý sơ cứu (Dùng biến 'firstAidSteps' đã sửa) */}
                  <div className={styles.detailItem}>
                    <h5>Gợi ý sơ cứu</h5>
                    <div className={styles.firstAidSteps}>
                      {firstAidSteps && firstAidSteps.length > 0 ? (
                        firstAidSteps.map((step, index) => (
                          <p key={index} className={styles.firstAidStep}>
                            <span>{index + 1}</span>
                            <span>{step}</span>
                          </p>
                        ))
                      ) : (
                        // Fallback: Nếu không tách được (ví dụ: "Chườm lạnh")
                        <p>{currentWound.firstAid || "Không có gợi ý."}</p>
                      )}
                    </div>
                  </div>
                  {/* Phần Nên làm */}
                  <div className={styles.detailItem}>
                    <h5>Nên làm</h5>
                    <div className={styles.firstAidSteps}>
                      {(() => {
                        const shouldDoSteps = currentWound.shouldDo
                          ?.split(/\d+\.\s+/)
                          .filter(Boolean)
                          .map((step) => step.trim());

                        return shouldDoSteps && shouldDoSteps.length > 0 ? (
                          shouldDoSteps.map((step, index) => (
                            <p
                              key={index}
                              // THÊM CLASS stepPositive TẠI ĐÂY
                              className={`${styles.firstAidStep} ${styles.stepPositive}`}
                            >
                              <span>{index + 1}</span>
                              <span>{step}</span>
                            </p>
                          ))
                        ) : (
                          <p>
                            {currentWound.shouldDo || "Không có thông tin."}
                          </p>
                        );
                      })()}
                    </div>
                  </div>

                  {/* Phần Không nên làm */}
                  <div className={styles.detailItem}>
                    <h5>Không nên làm</h5>
                    <div className={styles.firstAidSteps}>
                      {(() => {
                        const shouldNotDoSteps = currentWound.shouldNotDo
                          ?.split(/\d+\.\s+/)
                          .filter(Boolean)
                          .map((step) => step.trim());

                        return shouldNotDoSteps &&
                          shouldNotDoSteps.length > 0 ? (
                          shouldNotDoSteps.map((step, index) => (
                            <p
                              key={index}
                              // THÊM CLASS stepNegative TẠI ĐÂY
                              className={`${styles.firstAidStep} ${styles.stepNegative}`}
                            >
                              <span>{index + 1}</span>
                              <span>{step}</span>
                            </p>
                          ))
                        ) : (
                          <p>
                            {currentWound.shouldNotDo || "Không có thông tin."}
                          </p>
                        );
                      })()}
                    </div>
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

      {/* {currentWound && (
        <div className={styles.detailItem}>
          <h5>Nguồn</h5>
          <ul className={styles.sourceReliable}>
            <li>
              <strong>Tên:</strong>{" "}
              {currentWound.reliable_source.name || "Không rõ"}
            </li>
            <li>
              <strong>Ngày đăng:</strong>{" "}
              {currentWound.reliable_source.date
                ? new Date(
                    currentWound.reliable_source.date
                  ).toLocaleDateString("vi-VN")
                : "Không rõ"}
            </li>
            <li>
              <strong>Nguồn:</strong>{" "}
              {currentWound.reliable_source.url ? (
                <a
                  href={currentWound.reliable_source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {currentWound.reliable_source.url}
                </a>
              ) : (
                "Không có"
              )}
            </li>
          </ul>
        </div>
      )} */}
    </div>
  );
};

export default HistoryDetail;
