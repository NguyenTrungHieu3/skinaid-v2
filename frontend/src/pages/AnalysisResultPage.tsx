// src/pages/AnalysisResultPage.tsx
import React, { useEffect, useState } from "react";
import styles from "./AnalysisResultPage.module.css";
import AnalysisSidebar from "../components/analysis/AnalysisSidebar";
import MainHeader from "../components/analysis/MainHeader";
import MedicalDisclaimer from "../components/analysis/MedicalDisclaimer";
import AnalyzedImage from "../components/analysis/AnalyzedImage";
import AnalysisDetails from "../components/analysis/AnalysisDetails";
import TreatmentSection from "../components/analysis/TreatmentSection";
import { isAxiosError } from "axios";
import {
  getAnalysisResult,
  type AnalysisGetResponse,
  type SignificantWound,
} from "../services/aiService";
import { useParams } from "react-router-dom";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import DownloadModal from "../components/analysis/DownloadModal";
import AnalysisReportTemplate from "../components/analysis/AnalysisReportTemplate";
import {
  getMyProfile,
  type UserProfileResponse,
} from "../services/profileService";

// ... (Giữ nguyên các interface và hàm transformApiData)
type Severity = "Mild" | "Moderate" | "Severe" | string;
type WoundType = "abrasion" | "burn" | "bruise";
interface Tab {
  id: string;
  title: string;
  severity: Severity;
  type: WoundType;
}
interface SummaryCounts {
  total: number;
  abrasion: number;
  burn: number;
  bruise: number;
}

const transformApiData = (apiData: AnalysisGetResponse) => {
  // ... (Giữ nguyên logic cũ của bạn)
  const counts: SummaryCounts = { total: 0, abrasion: 0, burn: 0, bruise: 0 };
  const tabs: Tab[] = [];
  const typeIndices: { [key in WoundType]: number } = {
    abrasion: 1,
    burn: 1,
    bruise: 1,
  };
  apiData.significant_wounds.forEach((wound) => {
    const woundType = wound.wound_type as WoundType;
    if (!counts.hasOwnProperty(woundType)) return;
    counts.total++;
    counts[woundType]++;
    const currentIndex = typeIndices[woundType];
    const newId = `${woundType}_${currentIndex}`;
    typeIndices[woundType]++;
    tabs.push({
      id: newId,
      title: `${
        woundType.charAt(0).toUpperCase() + woundType.slice(1)
      } ${currentIndex}`,
      severity:
        wound.severity.charAt(0).toUpperCase() + wound.severity.slice(1),
      type: woundType,
    });
  });
  return { summaryCounts: counts, tabData: tabs };
};

const AnalysisResultPage = () => {
  const { analysis_id } = useParams<{ analysis_id: string }>();

  const [analysisData, setAnalysisData] = useState<AnalysisGetResponse | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [summaryCounts, setSummaryCounts] = useState<SummaryCounts>({
    total: 0,
    abrasion: 0,
    burn: 0,
    bruise: 0,
  });
  const [tabData, setTabData] = useState<Tab[]>([]);

  const [activeTab, setActiveTab] = useState<string>("");
  const [activeMainTab, setActiveMainTab] = useState<WoundType>("abrasion");
  const [isDownloadModalOpen, setIsDownloadModalOpen] = useState(false);

  // --- STATE MỚI: USER PROFILE ---
  const [userProfile, setUserProfile] = useState<UserProfileResponse | null>(
    null
  );

  // --- STATE MỚI: Danh sách vết thương cần in ra PDF ---
  const [woundsToExport, setWoundsToExport] = useState<SignificantWound[]>([]);

  useEffect(() => {
    if (!analysis_id) {
      setError("No Analysis ID provided.");
      setIsLoading(false);
      return;
    }
    const fetchResult = async () => {
      try {
        setIsLoading(true);
        const response = await getAnalysisResult(analysis_id);
        if (response.data.success) {
          const apiData = response.data.data;
          setAnalysisData(apiData);
          const { summaryCounts, tabData } = transformApiData(apiData);
          setSummaryCounts(summaryCounts);
          setTabData(tabData);

          // Mặc định khi mới load, woundsToExport là toàn bộ danh sách
          setWoundsToExport(apiData.significant_wounds);

          if (tabData.length > 0) {
            setActiveMainTab(tabData[0].type);
            setActiveTab(tabData[0].id);
          } else {
            setActiveMainTab("abrasion");
          }
        } else {
          setError(response.data.message);
        }

        // --- 2. THÊM ĐOẠN NÀY: GỌI API PROFILE ---
        try {
          // Gọi API lấy thông tin người dùng
          const profileResponse = await getMyProfile();
          if (profileResponse.data.success) {
            console.log("Profile loaded:", profileResponse.data.data); // Log để kiểm tra
            setUserProfile(profileResponse.data.data);
          }
        } catch (profileError) {
          // Nếu lỗi (ví dụ: 401 chưa đăng nhập), ta chỉ log ra và bỏ qua.
          // User vẫn xem được kết quả phân tích nhưng không có thông tin cá nhân.
          console.warn(
            "User not logged in or profile fetch failed (Guest mode)"
          );
          setUserProfile(null);
        }
      } catch (err) {
        if (isAxiosError(err))
          setError(err.response?.data?.message || "Failed to fetch.");
        else setError("Unknown error.");
      } finally {
        setIsLoading(false);
      }
    };
    fetchResult();
  }, [analysis_id]);

  const handleMainTabClick = (type: WoundType) => {
    setActiveMainTab(type);
    const firstTabInGroup = tabData.find((tab) => tab.type === type);
    if (firstTabInGroup) setActiveTab(firstTabInGroup.id);
  };

  const currentTabData = tabData.find((t) => t.id === activeTab);

  const getActiveWoundData = (): SignificantWound | null => {
    if (!analysisData || !currentTabData) return null;
    const parts = currentTabData.id.split("_");
    const type = parts[0] as WoundType;
    const index = parseInt(parts[1] || "1") - 1;
    const woundsOfType = analysisData.significant_wounds.filter(
      (w) => w.wound_type === type
    );
    return woundsOfType[index] || null;
  };

  const currentWoundData = getActiveWoundData();

  // --- HÀM TẠO PDF NHIỀU TRANG ---
  const generatePDF = async () => {
    // Chờ 1 chút để React render lại Template với woundsToExport mới
    await new Promise((resolve) => setTimeout(resolve, 100));

    const reportContainer = document.getElementById("skinaid-pdf-wrapper");
    if (!reportContainer) return;

    const images = Array.from(reportContainer.querySelectorAll("img"));

    // Tạo một Promise để chờ từng ảnh
    const imagePromises = images.map((img) => {
      const imageElement = img as HTMLImageElement;
      if (imageElement.complete) return Promise.resolve();
      return new Promise((resolve) => {
        imageElement.onload = resolve;
        imageElement.onerror = resolve; // Vẫn resolve dù lỗi để không treo PDF
      });
    });

    // Chờ tất cả ảnh tải xong mới chạy tiếp
    await Promise.all(imagePromises);

    // Tìm các trang (mỗi trang là 1 thẻ div class .pdf-page-to-print)
    const pages = document.querySelectorAll(".pdf-page-to-print");

    if (pages.length === 0) {
      alert("No report data found to generate.");
      return;
    }

    try {
      const pdf = new jsPDF("p", "mm", "a4");
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();

      for (let i = 0; i < pages.length; i++) {
        const pageElement = pages[i] as HTMLElement;

        // html2canvas chụp từng trang
        const canvas = await html2canvas(pageElement, {
          scale: 2,
          useCORS: true,
          logging: false,
          allowTaint: true,
          backgroundColor: "#ffffff",
          windowWidth: pageElement.scrollWidth,
          windowHeight: pageElement.scrollHeight,
        });

        const imgData = canvas.toDataURL("image/png");
        const imgWidth = canvas.width;
        const imgHeight = canvas.height;
        const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight);
        const imgX = (pdfWidth - imgWidth * ratio) / 2;
        const imgY = 0; // Top margin

        if (i > 0) pdf.addPage(); // Thêm trang mới nếu không phải trang đầu

        pdf.addImage(
          imgData,
          "PNG",
          imgX,
          imgY,
          imgWidth * ratio,
          imgHeight * ratio
        );
      }

      pdf.save(`SkinAid_Report_${analysisData?.file_name || "Result"}.pdf`);
    } catch (err) {
      console.error("PDF Error:", err);
      alert("Failed to generate PDF.");
    }
  };

  // --- XỬ LÝ KHI BẤM DOWNLOAD TRONG MODAL ---
  const handleDownloadConfirm = (
    format: "pdf" | "csv",
    selectedIndices: number[]
  ) => {
    if (!analysisData) return;

    if (format === "pdf") {
      // 1. Lọc danh sách các vết thương dựa trên index được chọn
      const selectedWounds = analysisData.significant_wounds.filter(
        (_, index) => selectedIndices.includes(index)
      );

      // 2. Cập nhật state để Template render lại đúng những vết thương này
      setWoundsToExport(selectedWounds);

      // 3. Gọi hàm tạo PDF (Hàm này có delay 100ms để đợi render)
      generatePDF();
    } else {
      alert("CSV export coming soon!");
    }
    setIsDownloadModalOpen(false);
  };

  // --- RENDER ---
  if (isLoading) return <div style={{ padding: "2rem" }}>Loading...</div>;
  if (error)
    return <div style={{ padding: "2rem", color: "red" }}>Error: {error}</div>;

  // 1. Nếu không có vết thương nào -> Hiển thị layout nhưng ẩn nút Download
  if (!analysisData || !currentWoundData || !currentTabData) {
    return (
      <div className={styles.analysisPage}>
        <AnalysisSidebar
          summaryCounts={summaryCounts}
          tabData={tabData}
          activeTab={activeTab}
          onTabClick={setActiveTab}
          activeMainTab={activeMainTab}
          onMainTabClick={handleMainTabClick}
        />
        <main className={styles.mainContent}>
          {/* Không truyền onDownload -> MainHeader sẽ tự ẩn nút */}
          <MainHeader title="No Wounds Detected" />
          <MedicalDisclaimer />
        </main>
      </div>
    );
  }

  // 2. Có vết thương -> Render đầy đủ
  return (
    <div className={styles.analysisPage}>
      <AnalysisSidebar
        summaryCounts={summaryCounts}
        tabData={[...tabData]}
        activeTab={activeTab}
        onTabClick={setActiveTab}
        activeMainTab={activeMainTab}
        onMainTabClick={handleMainTabClick}
      />

      <main className={styles.mainContent} id="analysis-report-content">
        <MainHeader
          title={currentTabData.title}
          severity={currentWoundData.severity}
          // Chỉ hiện nút download khi có vết thương
          onDownload={
            analysisData.significant_wounds.length > 0
              ? () => setIsDownloadModalOpen(true)
              : undefined
          }
        />
        <MedicalDisclaimer />

        <div className={styles.contentGrid}>
          <div className={styles.imageColumn}>
            <AnalyzedImage
              imageSrc={`http://localhost:8000${analysisData.image_url}`}
              boundingBox={currentWoundData.bounding_box}
              label={`${currentWoundData.wound_type} ${currentWoundData.confidence_score}`}
            />
          </div>
          <div className={styles.detailsColumn}>
            <AnalysisDetails
              likelihood={currentWoundData.confidence_score * 100}
              woundType={currentWoundData.wound_type}
              severity={currentWoundData.severity}
              healingTime={
                currentWoundData.firstaid_snapshot.estimated_healing_time ||
                "N/A"
              }
              supportItems={
                currentWoundData.firstaid_snapshot.supplies_needed || []
              }
            />
          </div>
        </div>
        {currentWoundData.firstaid_snapshot ? (
          <TreatmentSection snapshot={currentWoundData.firstaid_snapshot} />
        ) : (
          <div>No treatment data available.</div>
        )}

        <DownloadModal
          isOpen={isDownloadModalOpen}
          onClose={() => setIsDownloadModalOpen(false)}
          onDownload={handleDownloadConfirm}
          wounds={analysisData.significant_wounds} // Truyền toàn bộ danh sách vào Modal
        />
      </main>

      {/* TEMPLATE ẨN ĐỂ IN PDF */}
      {analysisData && (
        <AnalysisReportTemplate
          wounds={woundsToExport} // Chỉ render những vết thương đã chọn
          imageUrl={`http://localhost:8000${analysisData.image_url}`}
          reportId={analysis_id || "UNK"}
          fileName={analysisData.file_name}
          analyzedAt={analysisData.analyzed_at}
          userProfile={userProfile}
        />
      )}
    </div>
  );
};

export default AnalysisResultPage;
