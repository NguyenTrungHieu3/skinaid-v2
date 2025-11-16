import React, { useEffect, useState } from "react";
import styles from "./AnalysisResultPage.module.css"; // CSS cho layout 2 cột
import AnalysisSidebar from "../components/analysis/AnalysisSidebar"; // Import sidebar mới
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

// --- Dữ liệu giả (sẽ thay thế bằng API) ---
// --- Dữ liệu giả (ĐÃ SỬA LỖI: Thêm các trường bị thiếu) ---
// const analysisData = {
//   abrasion1: {
//     id: "abrasion1",
//     title: "Abrasion 1",
//     severity: "Mild",
//     type: "abrasion",
//     // --- DỮ LIỆU BỊ THIẾU ---
//     likelihood: 90,
//     healingTime: "6 days",
//     supportItems: ["Bandages", "Antibiotic ointment", "Mild soap"],
//     image: "/skinaid-sample-wound-1.jpg", // (Đảm bảo bạn có ảnh này)
//     firstaid_snapshot: {
//       title: "First Aid for Minor Abrasions",
//       steps: [
//         "Clean hands thoroughly with soap and water",
//         "Gently rinse wound with clean water or saline solution",
//         "Apply gentle pressure with clean cloth to stop bleeding",
//         "Apply thin layer of antibiotic ointment",
//         "Cover with sterile bandage",
//       ],
//       dos: ["Change bandage daily", "Watch for signs of infection"],
//       donts: ["Do not use hydrogen peroxide", "Do not pick at scabs"],
//     },
//   },
//   abrasion2: {
//     id: "abrasion2",
//     title: "Abrasion 2",
//     severity: "Mild",
//     type: "abrasion",
//     // --- DỮ LIỆU BỊ THIẾU ---
//     likelihood: 85,
//     healingTime: "4 days",
//     supportItems: ["Bandages", "Mild soap"],
//     image: "/skinaid-sample-wound-2.jpg",
//     firstaid_snapshot: {
//       title: "First Aid for Minor Abrasions",
//       steps: [
//         "Clean hands thoroughly with soap and water",
//         "Gently rinse wound with clean water or saline solution",
//         "Apply gentle pressure with clean cloth to stop bleeding",
//         "Apply thin layer of antibiotic ointment",
//         "Cover with sterile bandage",
//       ],
//       dos: ["Change bandage daily", "Watch for signs of infection"],
//       donts: ["Do not use hydrogen peroxide", "Do not pick at scabs"],
//     },
//   },
//   burn1: {
//     id: "burn1",
//     title: "Burn 1",
//     severity: "Moderate",
//     type: "burn",
//     // --- DỮ LIỆU BỊ THIẾU ---
//     likelihood: 95,
//     healingTime: "12 days",
//     supportItems: ["Cool compress", "Antibiotic ointment"],
//     image: "/skinaid-sample-wound-burn.jpg",
//     firstaid_snapshot: {
//       title: "First Aid for Minor Abrasions",
//       steps: [
//         "Clean hands thoroughly with soap and water",
//         "Gently rinse wound with clean water or saline solution",
//         "Apply gentle pressure with clean cloth to stop bleeding",
//         "Apply thin layer of antibiotic ointment",
//         "Cover with sterile bandage",
//       ],
//       dos: ["Change bandage daily", "Watch for signs of infection"],
//       donts: ["Do not use hydrogen peroxide", "Do not pick at scabs"],
//     },
//   },
//   bruise1: {
//     id: "bruise1",
//     title: "Bruise 1",
//     severity: "Mild",
//     type: "bruise",
//     // --- DỮ LIỆU BỊ THIẾU ---
//     likelihood: 70,
//     healingTime: "3 days",
//     supportItems: ["Ice pack", "Rest"],
//     image: "/skinaid-sample-wound-bruise.jpg",
//     firstaid_snapshot: {
//       title: "First Aid for Minor Abrasions",
//       steps: [
//         "Clean hands thoroughly with soap and water",
//         "Gently rinse wound with clean water or saline solution",
//         "Apply gentle pressure with clean cloth to stop bleeding",
//         "Apply thin layer of antibiotic ointment",
//         "Cover with sterile bandage",
//       ],
//       dos: ["Change bandage daily", "Watch for signs of infection"],
//       donts: ["Do not use hydrogen peroxide", "Do not pick at scabs"],
//     },
//   },
// };

// const tabData = [
//   {
//     id: "abrasion1",
//     title: "Abrasion 1",
//     severity: "Mild",
//     type: "abrasion",
//   },
//   {
//     id: "abrasion2",
//     title: "Abrasion 2",
//     severity: "Mild",
//     type: "abrasion",
//   },
//   { id: "burn1", title: "Burn 1", severity: "Moderate", type: "burn" },
//   { id: "bruise1", title: "Bruise 1", severity: "Mild", type: "bruise" }, // Thêm bruise
// ] as const;

// const summaryCounts = { total: 4, abrasion: 2, burn: 1, bruise: 1 }; // Cập nhật total

// --- Định nghĩa Types cho Sidebar (từ code cũ của bạn) ---
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

// --- HÀM HELPER: Chuyển dữ liệu API sang cho Sidebar ---
const transformApiData = (apiData: AnalysisGetResponse) => {
  const counts: SummaryCounts = { total: 0, abrasion: 0, burn: 0, bruise: 0 };
  const tabs: Tab[] = [];

  // --- SỬA LỖI: Thêm một bộ đếm index cho từng loại ---
  const typeIndices: { [key in WoundType]: number } = {
    abrasion: 1,
    burn: 1,
    bruise: 1,
  };

  // Lặp qua các vết thương AI tìm thấy
  apiData.significant_wounds.forEach((wound) => {
    // Ép kiểu wound_type về 1 trong 3 loại
    const woundType = wound.wound_type as WoundType;

    if (!counts.hasOwnProperty(woundType)) {
      return;
    }

    // 1. Cập nhật đếm
    counts.total++;
    counts[woundType]++;

    // --- SỬA LỖI: Lấy index hiện tại của loại đó ---
    const currentIndex = typeIndices[woundType];
    const newId = `${woundType}_${currentIndex}`;
    typeIndices[woundType]++; // Tăng index cho lần sau
    // ------------------------------------------

    // 2. Tạo tab item
    tabs.push({
      id: newId, // Tạo ID duy nhất, ví dụ: "abrasion_1"
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
  // 3. Lấy analysis_id từ URL
  const { analysis_id } = useParams<{ analysis_id: string }>();

  // State cho dữ liệu API
  const [analysisData, setAnalysisData] = useState<AnalysisGetResponse | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State cho Sidebar (lấy từ dữ liệu API)
  const [summaryCounts, setSummaryCounts] = useState<SummaryCounts>({
    total: 0,
    abrasion: 0,
    burn: 0,
    bruise: 0,
  });
  const [tabData, setTabData] = useState<Tab[]>([]);

  // State cho tab con (Abrasion 1, Burn 1, v.v.)
  // const [activeTab, setActiveTab] = useState("abrasion1"); // --- THÊM STATE CHO TAB CHÍNH ---
  // const [activeMainTab, setActiveMainTab] = useState<
  //   "abrasion" | "burn" | "bruise"
  // >("abrasion"); // Bắt đầu là 'abrasion'

  const [activeTab, setActiveTab] = useState<string>("");
  const [activeMainTab, setActiveMainTab] = useState<WoundType>("abrasion");

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
        const response = await getAnalysisResult(analysis_id);

        if (response.data.success) {
          const apiData = response.data.data;
          setAnalysisData(apiData);

          // 5. Biến đổi dữ liệu cho Sidebar
          const { summaryCounts, tabData } = transformApiData(apiData);
          setSummaryCounts(summaryCounts);
          setTabData(tabData);

          // 6. Set tab active mặc định
          if (tabData.length > 0) {
            setActiveMainTab(tabData[0].type); // Đặt tab chính
            setActiveTab(tabData[0].id); // Đặt tab con
          } else {
            // Không tìm thấy vết thương nào
            setActiveMainTab("abrasion"); // Set mặc định
          }
        } else {
          setError(response.data.message);
        }
      } catch (err) {
        if (isAxiosError(err)) {
          setError(err.response?.data?.message || "Failed to fetch analysis.");
        } else {
          setError("An unknown error occurred.");
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchResult();
  }, [analysis_id]); // Chạy lại khi ID thay đổi

  // const currentData = analysisData[activeTab as keyof typeof analysisData]; // --- THÊM HÀM XỬ LÝ KHI BẤM TAB CHÍNH ---

  const handleMainTabClick = (type: WoundType) => {
    setActiveMainTab(type);
    const firstTabInGroup = tabData.find((tab) => tab.type === type);
    if (firstTabInGroup) {
      setActiveTab(firstTabInGroup.id);
    }
  };

  // Xử lý trường hợp data chưa kịp tải
  // if (!currentData) {
  //   return <div>Loading...</div>; // Hoặc một spinner
  // }

  // --- LẤY DỮ LIỆU CHO NỘI DUNG CHÍNH ---
  // Tìm tab con (Abrasion 1) đang active
  const currentTabData = tabData.find((t) => t.id === activeTab);

  // Tìm vết thương (wound object) tương ứng với tab con đó
  const getActiveWoundData = (): SignificantWound | null => {
    if (!analysisData || !currentTabData) return null;

    // Logic tìm tab: "abrasion_1" -> index 0
    const parts = currentTabData.id.split("_");
    const type = parts[0] as WoundType;
    const index = parseInt(parts[1] || "1") - 1;

    const woundsOfType = analysisData.significant_wounds.filter(
      (w) => w.wound_type === type
    );
    return woundsOfType[index] || null;
  };

  const currentWoundData = getActiveWoundData();

  // --- RENDER ---
  if (isLoading) {
    return <div style={{ padding: "2rem" }}>Loading Analysis Result...</div>;
  }
  if (error) {
    return <div style={{ padding: "2rem", color: "red" }}>Error: {error}</div>;
  }
  if (!analysisData || !currentWoundData || !currentTabData) {
    // Xử lý trường hợp không tìm thấy vết thương nào
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
          <MainHeader title="No Wounds Detected" />
          <MedicalDisclaimer />
        </main>
      </div>
    );
  }

  return (
    // Layout 2 cột được định nghĩa trong CSS
    <div className={styles.analysisPage}>
      {/* --- 1. Sidebar (Trái) --- */}
      <AnalysisSidebar
        summaryCounts={summaryCounts}
        tabData={[...tabData]}
        activeTab={activeTab}
        onTabClick={setActiveTab}
        activeMainTab={activeMainTab}
        onMainTabClick={handleMainTabClick}
      />

      {/* --- 2. Nội dung chính (Phải) --- */}
      {/* (Theo yêu cầu, chỉ tập trung vào sidebar. 
          Đây là placeholder cho nội dung chính) */}
      <main className={styles.mainContent}>
        <MainHeader
          title={currentTabData.title}
          severity={currentWoundData.severity}
        />
        <MedicalDisclaimer />

        <div className={styles.contentGrid}>
          {/* 1. Cột ảnh (nhỏ hơn) */}
          <div className={styles.imageColumn}>
            <AnalyzedImage
              imageSrc={analysisData.image_url}
              boundingBox={currentWoundData.bounding_box}
              label={`${currentWoundData.wound_type} ${currentWoundData.confidence_score}`}
            />
          </div>
          {/* 2. Cột chi tiết (lớn hơn) */}
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
      </main>
    </div>
  );
};

export default AnalysisResultPage;
