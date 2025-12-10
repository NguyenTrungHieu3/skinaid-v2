import { useEffect, useState } from "react";
import styles from "./AnalysisResultPage.module.css";
import AnalysisSidebar from "../components/analysis/AnalysisSidebar";
import MainHeader from "../components/analysis/MainHeader";
import MedicalDisclaimer from "../components/analysis/MedicalDisclaimer";
import AnalyzedImage from "../components/analysis/AnalyzedImage";
import AnalysisDetails from "../components/analysis/AnalysisDetails";
import TreatmentSection from "../components/analysis/TreatmentSection";
import SeverityAlert from "../components/analysis/SeverityAlert";
import MapModal from "../components/analysis/MapModal";
import { isAxiosError } from "axios";
import {
  getAnalysisResult,
  type AnalysisGetResponse,
  type SignificantWound,
} from "../services/aiService";
import { BACKEND_URL } from "../services/api";
import { useParams } from "react-router-dom";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import DownloadModal from "../components/analysis/DownloadModal";
import AnalysisReportTemplate from "../components/analysis/AnalysisReportTemplate";
import {
  getMyProfile,
  type UserProfileResponse,
} from "../services/profileService";
import { useTranslation } from "react-i18next";

// --- Types ---
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

// --- Helper function to check if wound severity requires medical attention ---
const shouldShowMedicalFacility = (wounds: SignificantWound[]): boolean => {
  const severityLevels = ["moderate", "severe"];
  return wounds.some((wound) =>
    severityLevels.includes(wound.severity.toLowerCase())
  );
};

// Get the highest severity level from wounds
const getHighestSeverity = (wounds: SignificantWound[]): string => {
  if (wounds.some((w) => w.severity.toLowerCase() === "severe")) {
    return "severe";
  }
  if (wounds.some((w) => w.severity.toLowerCase() === "moderate")) {
    return "moderate";
  }
  return "mild";
};

// --- HÀM HELPER: Chuyển dữ liệu API sang cho Sidebar ---
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

    // 1. Format tên loại vết thương (Viết hoa chữ cái đầu)
    const formattedType =
      woundType.charAt(0).toUpperCase() + woundType.slice(1);

    // 2. Xử lý Subtype: Nếu có thì thêm dấu gạch ngang, nếu null thì chuỗi rỗng
    // Ví dụ kết quả: " - Scrape" hoặc ""
    const subTypeDisplay = wound.sub_type ? ` - ${wound.sub_type}` : "";

    tabs.push({
      id: newId,
      title: `${formattedType} ${currentIndex}${subTypeDisplay}`,
      severity:
        wound.severity.charAt(0).toUpperCase() + wound.severity.slice(1),
      type: woundType,
    });
  });
  return { summaryCounts: counts, tabData: tabs };
};

const AnalysisResultPage = () => {
  const { t } = useTranslation();

  const { analysis_id } = useParams<{ analysis_id: string }>();

  const [analysisData, setAnalysisData] = useState<AnalysisGetResponse | null>(
    null
  );
  const [, setIsLoading] = useState(true);
  const [, setError] = useState<string | null>(null);

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
  const [userProfile, setUserProfile] = useState<UserProfileResponse | null>(
    null
  );
  const [woundsToExport, setWoundsToExport] = useState<SignificantWound[]>([]);

  // State for MapModal
  const [isMapModalOpen, setIsMapModalOpen] = useState(false);

  // 4. Fetch dữ liệu khi component mount
  useEffect(() => {
    if (!analysis_id) {
      setError("No Analysis ID provided.");
      setIsLoading(false);
      return;
    }
    const fetchResult = async () => {
      try {
        setIsLoading(true);
        // 1. Fetch Analysis Result
        const response = await getAnalysisResult(analysis_id);
        if (response.data.success) {
          const apiData = response.data.data;
          setAnalysisData(apiData);
          const { summaryCounts, tabData } = transformApiData(apiData);
          setSummaryCounts(summaryCounts);
          setTabData(tabData);
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

        // 2. Fetch User Profile (Silent fail allowed)
        try {
          const profileResponse = await getMyProfile();
          if (profileResponse.data.success) {
            setUserProfile(profileResponse.data.data);
          }
        } catch (profileError) {
          console.warn("Guest mode or profile fetch failed");
          setUserProfile(null);
        }
      } catch (err) {
        if (isAxiosError(err))
          setError(err.response?.data?.message || "Failed to fetch.");
        else setError("Unknown error.");
      } finally {
        // Thêm timeout nhỏ để đảm bảo animation chạy mượt mà sau khi DOM mount
        setTimeout(() => setIsLoading(false), 300);
      }
    };
    fetchResult();
  }, [analysis_id]);

  // --- Handlers ---
  // --- LOGIC ĐIỀU HƯỚNG MỚI ---
  // const handleMainTabClick = (type: WoundType) => {
  //   setActiveMainTab(type);
  //   const firstTabInGroup = tabData.find((tab) => tab.type === type);
  //   if (firstTabInGroup) setActiveTab(firstTabInGroup.id);
  // };
  // --- LOGIC ĐIỀU HƯỚNG MỚI ---
  const handleMainTabClick = (type: WoundType) => {
    setActiveMainTab(type);
    const firstTabInGroup = tabData.find((tab) => tab.type === type);
    if (firstTabInGroup) setActiveTab(firstTabInGroup.id);
  };

  const _currentTabDataIndex = tabData.findIndex((t) => t.id === activeTab);
  void _currentTabDataIndex; // unused but kept for potential future use
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

  // --- PDF Generation Logic ---
  const generatePDF = async () => {
    await new Promise((resolve) => setTimeout(resolve, 100));
    const reportContainer = document.getElementById("skinaid-pdf-wrapper");
    if (!reportContainer) return;

    const images = Array.from(reportContainer.querySelectorAll("img"));
    const imagePromises = images.map((img) => {
      const imageElement = img as HTMLImageElement;
      if (imageElement.complete) return Promise.resolve();
      return new Promise((resolve) => {
        imageElement.onload = resolve;
        imageElement.onerror = resolve;
      });
    });

    await Promise.all(imagePromises);

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
        const canvas = await html2canvas(pageElement, {
          scale: 2,
          useCORS: true,
          logging: false,
          allowTaint: true,
          background: "#ffffff",
        } as any);

        const imgData = canvas.toDataURL("image/png");
        const imgWidth = canvas.width;
        const imgHeight = canvas.height;
        const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight);
        const imgX = (pdfWidth - imgWidth * ratio) / 2;

        if (i > 0) pdf.addPage();
        pdf.addImage(
          imgData,
          "PNG",
          imgX,
          0,
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

  const handleDownloadConfirm = (
    format: "pdf" | "csv",
    selectedIndices: number[]
  ) => {
    if (!analysisData) return;
    if (format === "pdf") {
      const selectedWounds = analysisData.significant_wounds.filter(
        (_, index) => selectedIndices.includes(index)
      );
      setWoundsToExport(selectedWounds);
      generatePDF();
    } else {
      alert("CSV export coming soon!");
    }
    setIsDownloadModalOpen(false);
  };

  // // --- Render Loading/Error ---
  // // Bạn có thể thêm animation skeleton ở đây nếu muốn pro hơn
  // if (isLoading)
  //   return <div className={styles.loadingContainer}>Loading analysis...</div>;
  // if (error) return <div className={styles.errorContainer}>Error: {error}</div>;

  // --- Render Empty State ---
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

  // --- Render Main Content ---
  return (
    <div className={styles.analysisPage}>
      <title>{t("title.analysis_result")}</title>
      <AnalysisSidebar
        summaryCounts={summaryCounts}
        tabData={[...tabData]}
        activeTab={activeTab}
        onTabClick={setActiveTab}
        activeMainTab={activeMainTab}
        onMainTabClick={handleMainTabClick}
      />

      <main className={styles.mainContent} id="analysis-report-content">
        {/* Header với Navigation */}
        <MainHeader
          // Tiêu đề và màu sắc
          title={currentTabData.title}
          severity={currentWoundData.severity}
          // Logic Dropdown mới
          tabs={tabData} // Truyền toàn bộ danh sách
          activeTabId={activeTab} // Tab đang chọn
          onSelectTab={(id) => {
            // Khi user chọn từ dropdown
            setActiveTab(id);
            // Tìm type của tab đó để update luôn Main Tab bên Sidebar
            const targetTab = tabData.find((t) => t.id === id);
            if (targetTab) setActiveMainTab(targetTab.type);
          }}
          // Logic Download
          onDownload={
            analysisData.significant_wounds.length > 0
              ? () => setIsDownloadModalOpen(true)
              : undefined
          }
        />

        <MedicalDisclaimer />

        <div className={styles.contentGrid}>
          {/* GROUP CHUNG 1 KHỐI VISUAL (Image + Details) */}
          <div className={styles.visualGroup}>
            <div className={styles.imageArea}>
              <AnalyzedImage
                imageSrc={`${BACKEND_URL}${analysisData.image_url}`}
                boundingBox={currentWoundData.bounding_box}
                label={`${currentWoundData.wound_type} ${currentWoundData.confidence_score}`}
              />
            </div>
            <div className={styles.detailsArea}>
              <AnalysisDetails
                likelihood={currentWoundData.confidence_score * 100}
                woundType={currentWoundData.wound_type}
                subType={currentWoundData.sub_type}
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
          wounds={analysisData.significant_wounds}
        />

        {/* Severity Alert - Shows when wound is moderate or severe */}
        {shouldShowMedicalFacility(analysisData.significant_wounds) && (
          <SeverityAlert
            severity={getHighestSeverity(analysisData.significant_wounds)}
            onFindFacility={() => setIsMapModalOpen(true)}
          />
        )}
      </main>

      {/* Hidden Template for PDF */}
      {analysisData && (
        <AnalysisReportTemplate
          wounds={woundsToExport}
          imageUrl={`${BACKEND_URL}${analysisData.image_url}`}
          reportId={analysis_id || "UNK"}
          fileName={analysisData.file_name}
          analyzedAt={analysisData.analyzed_at}
          userProfile={userProfile}
        />
      )}

      {/* Map Modal for finding nearby medical facilities */}
      <MapModal
        isOpen={isMapModalOpen}
        onClose={() => setIsMapModalOpen(false)}
      />
    </div>
  );
};

export default AnalysisResultPage;
