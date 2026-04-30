// components/analysis/WoundListItem.tsx
// Một item trong danh sách vết thương được phát hiện

import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import React, { useEffect, useRef } from "react";
import {
  Animated,
  Image,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import {
  DetectedWound,
  SEVERITY_CONFIG,
  getConfidenceColor,
} from "../../constants/analysisTypes";
import { Colors } from "../../constants/colors";

// Màu gradient cho mỗi loại vết thương
const WOUND_GRADIENTS: Record<string, [string, string]> = {
  tray:           ["#F5D0A9", "#E8A87C"],
  bam:            ["#6B8CAE", "#3D5472"],
  bong:           ["#8B7355", "#4A4035"],
  "mun-trung-ca": ["#D4B896", "#C4A882"],
  "vay-nen":      ["#E0C9A8", "#D4B896"],
  "nam-da":       ["#C4A070", "#B89060"],
};

// Icon cho mỗi loại mức độ
const SEVERITY_ICONS: Record<string, string> = {
  NHE:        "shield",
  TRUNG_BINH: "alert-triangle",
  NANG:       "alert-octagon",
};

interface Props {
  wound: DetectedWound;
  imageUri?: string;
  onToggle: (id: string) => void;
  animDelay?: number;
}

export default function WoundListItem({
  wound,
  imageUri,
  onToggle,
  animDelay = 0,
}: Props) {
  const severity = wound.severity ? SEVERITY_CONFIG[wound.severity] : null;
  const confidenceColor = getConfidenceColor(wound.confidence);
  const gradientColors = WOUND_GRADIENTS[wound.woundTypeId] ?? ["#C0C0C0", "#909090"];

  // ── Entrance animation ──────────────────────────────────────────
  const translateY = useRef(new Animated.Value(40)).current;
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, {
        toValue: 1,
        duration: 400,
        delay: animDelay,
        useNativeDriver: true,
      }),
      Animated.spring(translateY, {
        toValue: 0,
        delay: animDelay,
        damping: 16,
        stiffness: 110,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  // ── Checkbox bounce animation ────────────────────────────────────
  const checkScale = useRef(new Animated.Value(wound.selected ? 1 : 0.85)).current;
  const cardScale  = useRef(new Animated.Value(1)).current;

  const handleToggle = () => {
    // Card micro-press
    Animated.sequence([
      Animated.timing(cardScale, { toValue: 0.975, duration: 60, useNativeDriver: true }),
      Animated.spring(cardScale, { toValue: 1, damping: 14, stiffness: 220, useNativeDriver: true }),
    ]).start();
    // Checkbox bounce
    Animated.sequence([
      Animated.timing(checkScale, { toValue: 0.65, duration: 70, useNativeDriver: true }),
      Animated.spring(checkScale, {
        toValue: wound.selected ? 0.85 : 1,
        damping: 11,
        stiffness: 210,
        useNativeDriver: true,
      }),
    ]).start();
    onToggle(wound.id);
  };

  const confidencePct = Math.min(wound.confidence, 100);
  const severityIcon = (wound.severity ? (SEVERITY_ICONS[wound.severity] ?? "info") : "info") as any;

  return (
    <Animated.View
      style={[
        styles.container,
        wound.selected && styles.containerSelected,
        { opacity, transform: [{ translateY }, { scale: cardScale }] },
      ]}
    >
      <TouchableOpacity
        style={styles.inner}
        onPress={handleToggle}
        activeOpacity={0.92}
      >
        {/* ── Left: Thumbnail ────────────────────────────────────── */}
        <View style={styles.thumbnailWrapper}>
          <LinearGradient
            colors={gradientColors}
            style={styles.thumbnailGradient}
          >
            {imageUri ? (
              <Image source={{ uri: imageUri }} style={styles.thumbnailImage} />
            ) : null}
            {/* Gradient overlay bottom */}
            <LinearGradient
              colors={["transparent", "rgba(0,0,0,0.52)"]}
              style={styles.thumbnailOverlay}
            />
          </LinearGradient>

          {/* Số thứ tự badge */}
          <View style={[styles.indexBadge, wound.selected && styles.indexBadgeSelected]}>
            <Text style={styles.indexBadgeText}>#{wound.index}</Text>
          </View>
        </View>

        {/* ── Center: Content ────────────────────────────────────── */}
        <View style={styles.content}>
          {/* Tiêu đề vết */}
          <View style={styles.titleRow}>
            <Text style={styles.woundLabel}>Vết {wound.index}</Text>
            <Text style={styles.woundName} numberOfLines={1}>
              {wound.woundType}
            </Text>
          </View>

          {/* Badge mức độ nghiêm trọng — chỉ hiện nếu có severity */}
          {severity ? (
            <View style={[styles.severityPill, { backgroundColor: severity.bgColor }]}>
              <Feather
                name={severityIcon}
                size={9}
                color={severity.color}
                style={{ marginRight: 3 }}
              />
              <Text style={[styles.severityText, { color: severity.color }]}>
                {severity.label}
              </Text>
            </View>
          ) : (
            <View style={[styles.severityPill, { backgroundColor: "#EFF6FF" }]}>
              <Feather
                name="activity"
                size={9}
                color="#3B82F6"
                style={{ marginRight: 3 }}
              />
              <Text style={[styles.severityText, { color: "#3B82F6" }]}>
                BỆNH DA LIỄU
              </Text>
            </View>
          )}

          {/* Confidence bar */}
          <View style={styles.confidenceSection}>
            <View style={styles.confidenceHeader}>
              <Text style={styles.confidenceLabel}>Độ tin cậy</Text>
              <Text style={[styles.confidenceValue, { color: confidenceColor }]}>
                {wound.confidence.toFixed(1)}%
              </Text>
            </View>
            <View style={styles.confidenceTrack}>
              <View
                style={[
                  styles.confidenceFill,
                  {
                    width: `${confidencePct}%` as any,
                    backgroundColor: confidenceColor,
                  },
                ]}
              />
            </View>
          </View>
        </View>

        {/* ── Right: Checkbox ────────────────────────────────────── */}
        <Animated.View
          style={[
            styles.checkbox,
            wound.selected && styles.checkboxSelected,
            { transform: [{ scale: checkScale }] },
          ]}
        >
          {wound.selected && (
            <Feather name="check" size={15} color={Colors.white} />
          )}
        </Animated.View>
      </TouchableOpacity>

      {/* Selected accent bar on left edge */}
      {wound.selected && <View style={styles.selectedAccentBar} />}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 12,
    marginBottom: 8,
    borderRadius: 14,
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 1.5,
    borderColor: Colors.borderLight,
    overflow: "hidden",
  },
  containerSelected: {
    borderColor: Colors.primary,
    // backgroundColor: "rgba(2,161,141,0.04)",
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 3,
  },

  // ── Accent bar ───────────────────────────────────────────────────
  selectedAccentBar: {
    position: "absolute",
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
    backgroundColor: Colors.primary,
    borderTopLeftRadius: 14,
    borderBottomLeftRadius: 14,
  },

  // ── Inner layout ─────────────────────────────────────────────────
  inner: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
    paddingLeft: 12,
    paddingRight: 14,
    gap: 12,
  },

  // ── Thumbnail ────────────────────────────────────────────────────
  thumbnailWrapper: {
    position: "relative",
  },
  thumbnailGradient: {
    width: 72,
    height: 78,
    borderRadius: 12,
    overflow: "hidden",
    justifyContent: "flex-end",
  },
  thumbnailImage: {
    ...StyleSheet.absoluteFillObject,
    resizeMode: "cover",
  },
  thumbnailOverlay: {
    height: 36,
    width: "100%",
  },
  indexBadge: {
    position: "absolute",
    top: 6,
    left: 6,
    backgroundColor: "rgba(0,0,0,0.48)",
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  indexBadgeSelected: {
    backgroundColor: Colors.primary,
  },
  indexBadgeText: {
    color: Colors.white,
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.3,
  },

  // ── Content ──────────────────────────────────────────────────────
  content: {
    flex: 1,
    gap: 6,
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 5,
  },
  woundLabel: {
    fontSize: 11,
    fontWeight: "500",
    color: Colors.textMuted,
    letterSpacing: 0.2,
  },
  woundName: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.textPrimary,
    flexShrink: 1,
    letterSpacing: 0.1,
  },

  // ── Severity pill ────────────────────────────────────────────────
  severityPill: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 20,
  },
  severityText: {
    fontSize: 9.5,
    fontWeight: "800",
    letterSpacing: 0.4,
    textTransform: "uppercase",
  },

  // ── Confidence ───────────────────────────────────────────────────
  confidenceSection: {
    gap: 4,
  },
  confidenceHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  confidenceLabel: {
    fontSize: 10.5,
    color: Colors.textMuted,
    fontWeight: "500",
  },
  confidenceValue: {
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.2,
  },
  confidenceTrack: {
    height: 5,
    backgroundColor: Colors.backgroundTertiary,
    borderRadius: 10,
    overflow: "hidden",
  },
  confidenceFill: {
    height: "100%",
    borderRadius: 10,
  },

  // ── Checkbox ─────────────────────────────────────────────────────
  checkbox: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 2,
    borderColor: Colors.borderLight,
    backgroundColor: Colors.backgroundTertiary,
    alignItems: "center",
    justifyContent: "center",
  },
  checkboxSelected: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.4,
    shadowRadius: 6,
    elevation: 4,
  },
});
