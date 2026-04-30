// components/analysis/AnalysisSummaryCard.tsx
// Card tổng quan: ảnh với bounding boxes + thống kê số lượng, độ chính xác, loại, nghiêm trọng

import React, { useRef } from "react";
import {
  Animated,
  Image,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from "react-native";
import { Colors } from "../../constants/colors";
import { AnalysisResult, DetectedWound } from "../../constants/analysisTypes";

interface Props {
  result: AnalysisResult;
  scrollY: Animated.Value;
}

/** Vẽ bounding box overlay trên ảnh */
function BoundingBoxOverlay({
  wounds,
  imageWidth,
  imageHeight,
}: {
  wounds: DetectedWound[];
  imageWidth: number;
  imageHeight: number;
}) {
  return (
    <>
      {wounds.map((w, idx) => {
        const left = w.boundingBox.x * imageWidth;
        const top = w.boundingBox.y * imageHeight;
        const width = w.boundingBox.width * imageWidth;
        const height = w.boundingBox.height * imageHeight;
        // Màu teal với opacity khác nhau theo index
        const borderColor =
          idx === 0 ? Colors.primary : idx === 1 ? Colors.primaryLight : "#6EE7D0";
        return (
          <View
            key={w.id}
            style={[
              styles.bbox,
              { left, top, width, height, borderColor },
            ]}
          >
            {/* Label index góc trái trên */}
            <View style={[styles.bboxLabel, { backgroundColor: borderColor }]}>
              <Text style={styles.bboxLabelText}>{w.index}</Text>
            </View>
          </View>
        );
      })}
    </>
  );
}

export default function AnalysisSummaryCard({ result, scrollY }: Props) {
  const { width } = useWindowDimensions();
  // Ảnh chiếm full chiều ngang trừ padding
  const IMAGE_WIDTH = width - 32; // px
  const IMAGE_HEIGHT = 200;       // px cố định

  // Hiệu ứng parallax nhẹ khi scroll
  const imageTranslate = scrollY.interpolate({
    inputRange: [0, 150],
    outputRange: [0, -30],
    extrapolate: "clamp",
  });

  return (
    <View style={styles.card}>
      {/* Header label */}
      <Text style={styles.sectionLabel}>KẾT QUẢ PHÂN TÍCH</Text>

      {/* Ảnh + bounding boxes */}
      <View style={[styles.imageContainer, { height: IMAGE_HEIGHT }]}>
        <Animated.View
          style={[
            StyleSheet.absoluteFill,
            { transform: [{ translateY: imageTranslate }] },
          ]}
        >
          {result.imageUri ? (
            <Image
              source={{ uri: result.imageUri }}
              style={styles.image}
              resizeMode="cover"
            />
          ) : (
            // Placeholder khi chưa có ảnh thật
            <View style={styles.imagePlaceholder} />
          )}
        </Animated.View>

        {/* Bounding boxes overlay */}
        <BoundingBoxOverlay
          wounds={result.wounds}
          imageWidth={IMAGE_WIDTH}
          imageHeight={IMAGE_HEIGHT}
        />

        {/* Gradient overlay dưới cùng để text đọc được */}
        <View style={styles.imageBottomGradient} />
      </View>

      {/* Thống kê: Số lượng + Độ chính xác */}
      <View style={styles.statsGrid}>
        <View style={styles.statRow}>
          <Text style={styles.statLabel}>Số lượng:</Text>
          <Text style={styles.statValuePrimary}>{result.totalWounds}</Text>
        </View>
        <View style={styles.divider} />
        <View style={styles.statRow}>
          <Text style={styles.statLabel}>Độ chính xác TB:</Text>
          <Text style={styles.statValuePrimary}>
            {result.averageConfidence.toFixed(2)}%
          </Text>
        </View>
      </View>

      {/* Grid: Loại + Nghiêm trọng */}
      <View style={styles.typeGrid}>
        <View style={styles.typeCell}>
          <Text style={styles.typeCellHeader}>LOẠI</Text>
          <Text style={styles.typeCellValue} numberOfLines={1}>
            {result.primaryWoundType}
          </Text>
        </View>
        <View style={styles.typeCellDivider} />
        <View style={styles.typeCell}>
          <Text style={styles.typeCellHeader}>NGHIÊM TRỌNG</Text>
          <Text style={[styles.typeCellValue, styles.typeCellSevere]} numberOfLines={1}>
            {result.mostSevereWound}
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 16,
    marginTop: 16,
    backgroundColor: Colors.white,
    borderRadius: 20,
    overflow: "hidden",
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 4,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: Colors.textMuted,
    letterSpacing: 1.2,
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 10,
  },
  // ── Image ──────────────────────────────────────
  imageContainer: {
    width: "100%",
    overflow: "hidden",
    position: "relative",
  },
  image: {
    width: "100%",
    height: "120%", // Cho phép parallax translate
    position: "absolute",
    top: 0,
    left: 0,
  },
  imagePlaceholder: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "#C9A882",  // Màu da gần giống ảnh mẫu
  },
  imageBottomGradient: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    height: 40,
    backgroundColor: "rgba(0,0,0,0.15)",
  },
  // ── Bounding boxes ─────────────────────────────
  bbox: {
    position: "absolute",
    borderWidth: 2,
    borderRadius: 2,
  },
  bboxLabel: {
    position: "absolute",
    top: -1,
    left: -1,
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 2,
    minWidth: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  bboxLabelText: {
    color: "#fff",
    fontSize: 9,
    fontWeight: "700",
  },
  // ── Stats ──────────────────────────────────────
  statsGrid: {
    paddingHorizontal: 16,
    paddingTop: 14,
  },
  statRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 8,
  },
  statLabel: {
    fontSize: 13,
    color: Colors.textLight,
    fontWeight: "400",
  },
  statValuePrimary: {
    fontSize: 15,
    color: Colors.primary,
    fontWeight: "700",
  },
  divider: {
    height: 1,
    backgroundColor: Colors.backgroundTertiary,
    marginHorizontal: -4,
  },
  // ── Type grid ──────────────────────────────────
  typeGrid: {
    flexDirection: "row",
    marginHorizontal: 16,
    marginTop: 12,
    marginBottom: 14,
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 10,
    overflow: "hidden",
  },
  typeCell: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    gap: 3,
  },
  typeCellDivider: {
    width: 1,
    backgroundColor: Colors.borderLight,
  },
  typeCellHeader: {
    fontSize: 9,
    fontWeight: "700",
    color: Colors.textMuted,
    letterSpacing: 0.8,
    textTransform: "uppercase",
  },
  typeCellValue: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.textPrimary,
  },
  typeCellSevere: {
    color: Colors.error,
  },
});
