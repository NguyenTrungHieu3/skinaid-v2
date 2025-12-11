import { useState } from "react";
import styles from "./DownloadModal.module.css"; // Reuse existing modal styles
import { FaTimes, FaSignInAlt, FaUserPlus, FaSave } from "react-icons/fa";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { claimAnalysis } from "../../services/guestService";
import { useAuth } from "../../contexts/AuthContext";

interface SaveLoginModalProps {
    isOpen: boolean;
    onClose: () => void;
    analysisId: string;
    onSaveSuccess?: () => void;
}

const SaveLoginModal = ({
    isOpen,
    onClose,
    analysisId,
    onSaveSuccess,
}: SaveLoginModalProps) => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    if (!isOpen) return null;

    const handleLogin = () => {
        // Lưu analysisId vào sessionStorage để claim sau khi login
        sessionStorage.setItem("pendingClaimAnalysisId", analysisId);
        onClose();
        navigate("/login", { state: { returnTo: `/analysis-result/${analysisId}` } });
    };

    const handleRegister = () => {
        // Lưu analysisId vào sessionStorage để claim sau khi register
        sessionStorage.setItem("pendingClaimAnalysisId", analysisId);
        onClose();
        navigate("/register", { state: { returnTo: `/analysis-result/${analysisId}` } });
    };

    const handleSaveNow = async () => {
        // Chỉ gọi khi đã đăng nhập
        if (!isAuthenticated) {
            return;
        }

        setIsSaving(true);
        setError(null);

        try {
            await claimAnalysis(analysisId);
            setSuccess(true);
            onSaveSuccess?.();

            // Tự động đóng sau 2 giây
            setTimeout(() => {
                onClose();
            }, 2000);
        } catch (err: any) {
            console.error("Error claiming analysis:", err);
            setError(
                err.response?.data?.message ||
                t("save_modal.error_generic", "Không thể lưu kết quả. Vui lòng thử lại.")
            );
        } finally {
            setIsSaving(false);
        }
    };

    // Nếu đã đăng nhập, hiển thị UI xác nhận lưu
    if (isAuthenticated) {
        return (
            <div className={styles.overlay}>
                <div className={styles.modal}>
                    <div className={styles.header}>
                        <h3>{t("save_modal.title_authenticated", "Lưu kết quả phân tích")}</h3>
                        <button onClick={onClose} className={styles.closeBtn}>
                            <FaTimes />
                        </button>
                    </div>

                    {success ? (
                        <div style={{ padding: "20px", textAlign: "center" }}>
                            <div style={{ fontSize: "48px", color: "#27ae60", marginBottom: "10px" }}>✓</div>
                            <p style={{ color: "#27ae60", fontWeight: "bold" }}>
                                {t("save_modal.success", "Đã lưu thành công vào lịch sử của bạn!")}
                            </p>
                        </div>
                    ) : (
                        <>
                            <p className={styles.subtitle}>
                                {t("save_modal.confirm_save", "Bạn có muốn lưu kết quả này vào lịch sử phân tích?")}
                            </p>

                            {error && (
                                <div style={{ color: "#e74c3c", padding: "10px", marginBottom: "10px" }}>
                                    {error}
                                </div>
                            )}

                            <div className={styles.actions}>
                                <button onClick={onClose} className={styles.btnCancel}>
                                    {t("save_modal.cancel", "Hủy")}
                                </button>
                                <button
                                    onClick={handleSaveNow}
                                    className={styles.btnDownload}
                                    disabled={isSaving}
                                >
                                    {isSaving ? (
                                        t("save_modal.saving", "Đang lưu...")
                                    ) : (
                                        <>
                                            <FaSave style={{ marginRight: "5px" }} />
                                            {t("save_modal.save", "Lưu")}
                                        </>
                                    )}
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>
        );
    }

    // UI cho guest user - yêu cầu đăng nhập
    return (
        <div className={styles.overlay}>
            <div className={styles.modal}>
                <div className={styles.header}>
                    <h3>{t("save_modal.title_guest", "Lưu kết quả phân tích")}</h3>
                    <button onClick={onClose} className={styles.closeBtn}>
                        <FaTimes />
                    </button>
                </div>

                <p className={styles.subtitle}>
                    {t("save_modal.guest_message", "Để lưu kết quả phân tích vào lịch sử, bạn cần đăng nhập hoặc đăng ký tài khoản.")}
                </p>

                <div style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "12px",
                    padding: "0 20px 20px"
                }}>
                    <button
                        onClick={handleLogin}
                        style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            gap: "8px",
                            padding: "12px 24px",
                            backgroundColor: "#3498db",
                            color: "white",
                            border: "none",
                            borderRadius: "8px",
                            fontSize: "16px",
                            cursor: "pointer",
                            transition: "background-color 0.2s",
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = "#2980b9"}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "#3498db"}
                    >
                        <FaSignInAlt />
                        {t("save_modal.login_button", "Đăng nhập")}
                    </button>

                    <button
                        onClick={handleRegister}
                        style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            gap: "8px",
                            padding: "12px 24px",
                            backgroundColor: "#27ae60",
                            color: "white",
                            border: "none",
                            borderRadius: "8px",
                            fontSize: "16px",
                            cursor: "pointer",
                            transition: "background-color 0.2s",
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = "#219a52"}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "#27ae60"}
                    >
                        <FaUserPlus />
                        {t("save_modal.register_button", "Đăng ký tài khoản")}
                    </button>
                </div>

                <div className={styles.actions} style={{ borderTop: "1px solid #eee", paddingTop: "15px" }}>
                    <button onClick={onClose} className={styles.btnCancel} style={{ width: "100%" }}>
                        {t("save_modal.cancel_guest", "Để sau")}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SaveLoginModal;
