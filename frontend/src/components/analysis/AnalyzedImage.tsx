import React, { useState } from "react";
import styles from "./AnalyzedImage.module.css";
import { FaCamera } from "react-icons/fa";

// 1. ĐỊNH NGHĨA TYPE CHO PROPS (NHẬN TỪ TRANG CHA)
interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface AnalyzedImageProps {
  imageSrc: string; // URL ảnh từ API
  boundingBox?: BoundingBox; // Tọa độ (px)
  label?: string; // Nhãn (vd: "abrasion 1.0")
}

// 2. STATE ĐỂ LƯU KÍCH THƯỚC GỐC CỦA ẢNH
const AnalyzedImage = ({
  imageSrc,
  boundingBox,
  label,
}: AnalyzedImageProps) => {
  const [dimensions, setDimensions] = useState<{
    naturalWidth: number;
    naturalHeight: number;
  } | null>(null); // 3. HÀM CHẠY KHI ẢNH ĐƯỢC TẢI XONG

  const handleImageLoad = (
    e: React.SyntheticEvent<HTMLImageElement, Event>
  ) => {
    // Lấy kích thước GỐC (natural) của ảnh
    const { naturalWidth, naturalHeight } = e.currentTarget;
    setDimensions({ naturalWidth, naturalHeight });
  }; // 4. HÀM TÍNH TOÁN STYLE MỚI (CHO CẢ BOX VÀ LABEL)

  const calculateStyles = () => {
    if (!boundingBox || !dimensions) {
      return { boxStyle: { display: "none" }, labelStyle: { display: "none" } };
    }

    // Tính toán %
    const topPct = (boundingBox.y / dimensions.naturalHeight) * 100;
    const leftPct = (boundingBox.x / dimensions.naturalWidth) * 100;
    const widthPct = (boundingBox.width / dimensions.naturalWidth) * 100;
    const heightPct = (boundingBox.height / dimensions.naturalHeight) * 100;

    // Style cho Bounding Box
    const boxStyle: React.CSSProperties = {
      top: `${topPct}%`,
      left: `${leftPct}%`,
      width: `${widthPct}%`,
      height: `${heightPct}%`,
    };

    // --- LOGIC "THÔNG MINH" CHO LABEL ---
    let labelStyle: React.CSSProperties = {};

    // Nếu box nằm quá sát mép trên (ví dụ: top < 5%)
    // Label sẽ bị 'overflow: hidden' cắt mất
    if (topPct < 5) {
      // -> Đặt label BÊN TRONG (góc trên bên trái)
      labelStyle = {
        top: "0px",
        left: "0px",
        transform: "translate(2px, 2px)", // Đẩy vào 1 chút
        borderRadius: "4px 0 4px 0", // Bo góc chéo
      };
    } else {
      // -> Đặt label BÊN NGOÀI (như cũ)
      labelStyle = {
        bottom: "100%",
        left: "-2px", // Căn với viền
        marginBottom: "4px", // Khoảng cách
        borderRadius: "4px",
      };
    }

    return { boxStyle, labelStyle };
  };

  // 5. Lấy style đã tính toán
  const { boxStyle, labelStyle } = calculateStyles();

  return (
    <div className={styles.imageCard}>
      <h3 className={styles.panelTitle}>
        <FaCamera /> Analyzed Image    
      </h3>
      <div className={styles.imageWrapper}>
        <img
          src={imageSrc}
          alt="Analyzed wound"
          onLoad={handleImageLoad} // Gắn hàm load
          onError={(e) => {
            e.currentTarget.src =
              "https://placehold.co/600x600/eee/ccc?text=Image+Not+Found";
          }}
        />
        {/* 6. BOUNDING BOX (Dùng style động) */} 
        <div className={styles.boundingBox} style={boxStyle}>
          {/* 7. LABEL (Dùng style động) */}
          <span className={styles.boundingBoxLabel} style={labelStyle}>
            {label} 
          </span>
        </div>
      </div>
    </div>
  );
};

export default AnalyzedImage;
