/**
 * RouteStepsSheet.tsx
 * Modal bottom sheet displaying turn-by-turn navigation steps from the route API.
 * Slides in from the bottom with a semi-transparent backdrop.
 */

import { Feather } from "@expo/vector-icons";
import React, { useEffect, useRef } from "react";
import {
  Animated,
  Dimensions,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { RouteData, RouteStep } from "../../services/mapService";

const { height: SCREEN_HEIGHT } = Dimensions.get("window");
const SHEET_HEIGHT = SCREEN_HEIGHT * 0.6;

interface RouteStepsSheetProps {
  visible: boolean;
  routeData: RouteData | null;
  destinationName: string;
  onClose: () => void;
}

function StepItem({ step, index }: { step: RouteStep; index: number }) {
  const distText =
    step.distance < 1000
      ? `${Math.round(step.distance)} m`
      : `${(step.distance / 1000).toFixed(1)} km`;

  const durText =
    step.duration < 60
      ? `${Math.round(step.duration)} giây`
      : `${Math.round(step.duration / 60)} phút`;

  /* Simple icon mapping based on instruction keywords */
  let icon: keyof typeof Feather.glyphMap = "arrow-up";
  const lower = step.instruction.toLowerCase();
  if (lower.includes("trái") || lower.includes("left")) icon = "corner-up-left";
  else if (lower.includes("phải") || lower.includes("right")) icon = "corner-up-right";
  else if (lower.includes("vòng") || lower.includes("roundabout")) icon = "refresh-cw";
  else if (lower.includes("đến") || lower.includes("arrive")) icon = "map-pin";

  return (
    <View style={styles.stepItem}>
      <View style={styles.stepConnector}>
        <View style={styles.stepDot}>
          <Feather name={icon} size={14} color="#3DBFA0" />
        </View>
        {index > 0 && <View style={styles.stepLine} />}
      </View>
      <View style={styles.stepContent}>
        <Text style={styles.stepInstruction}>{step.instruction}</Text>
        <View style={styles.stepMeta}>
          <Text style={styles.stepDist}>{distText}</Text>
          <Text style={styles.stepSep}>·</Text>
          <Text style={styles.stepDur}>{durText}</Text>
        </View>
      </View>
    </View>
  );
}

export default function RouteStepsSheet({
  visible,
  routeData,
  destinationName,
  onClose,
}: RouteStepsSheetProps) {
  const translateY = useRef(new Animated.Value(SHEET_HEIGHT)).current;
  const backdropOpacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.spring(translateY, {
          toValue: 0,
          tension: 65,
          friction: 11,
          useNativeDriver: true,
        }),
        Animated.timing(backdropOpacity, {
          toValue: 0.45,
          duration: 280,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(translateY, {
          toValue: SHEET_HEIGHT,
          duration: 260,
          useNativeDriver: true,
        }),
        Animated.timing(backdropOpacity, {
          toValue: 0,
          duration: 220,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visible]);

  const totalDistText =
    routeData?.distance_km != null
      ? `${routeData.distance_km.toFixed(1)} km`
      : "";

  const totalDurText =
    routeData?.duration_minutes != null
      ? routeData.duration_minutes < 60
        ? `${Math.round(routeData.duration_minutes)} phút`
        : `${Math.floor(routeData.duration_minutes / 60)} giờ ${Math.round(routeData.duration_minutes % 60)} phút`
      : "";

  return (
    <Modal
      visible={visible}
      transparent
      animationType="none"
      onRequestClose={onClose}
      statusBarTranslucent
    >
      {/* Backdrop */}
      <Pressable style={StyleSheet.absoluteFillObject} onPress={onClose}>
        <Animated.View
          style={[
            styles.backdrop,
            { opacity: backdropOpacity },
          ]}
        />
      </Pressable>

      {/* Sheet */}
      <Animated.View
        style={[styles.sheet, { transform: [{ translateY }] }]}
        pointerEvents="box-none"
      >
        {/* Handle */}
        <View style={styles.handle} />

        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <View style={styles.headerIcon}>
              <Feather name="navigation" size={16} color="#FFFFFF" />
            </View>
            <View>
              <Text style={styles.headerTitle} numberOfLines={1}>
                {destinationName || "Đường đi"}
              </Text>
              {(totalDistText || totalDurText) && (
                <Text style={styles.headerSub}>
                  {[totalDistText, totalDurText].filter(Boolean).join("  ·  ")}
                </Text>
              )}
            </View>
          </View>
          <Pressable style={styles.closeBtn} onPress={onClose}>
            <Feather name="x" size={18} color="#374151" />
          </Pressable>
        </View>

        {/* Route summary badge */}
        {routeData?.summary ? (
          <View style={styles.summaryBadge}>
            <Feather name="map" size={12} color="#3DBFA0" />
            <Text style={styles.summaryText}>{routeData.summary}</Text>
          </View>
        ) : null}

        {/* Steps list */}
        <ScrollView
          style={styles.stepsList}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.stepsContent}
        >
          {(routeData?.steps ?? []).map((step, idx) => (
            <StepItem key={idx} step={step} index={idx} />
          ))}
          {(routeData?.steps?.length ?? 0) === 0 && (
            <View style={styles.emptyState}>
              <Feather name="map" size={40} color="#D1D5DB" />
              <Text style={styles.emptyText}>Không có bước chỉ đường</Text>
            </View>
          )}
        </ScrollView>
      </Animated.View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "#000000",
  },
  sheet: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    height: SHEET_HEIGHT,
    backgroundColor: "#FFFFFF",
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 20,
    paddingBottom: 24,
  },
  handle: {
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: "#E5E7EB",
    alignSelf: "center",
    marginTop: 10,
    marginBottom: 16,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  headerLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    flex: 1,
  },
  headerIcon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: "#3DBFA0",
    alignItems: "center",
    justifyContent: "center",
  },
  headerTitle: {
    fontSize: 15,
    fontWeight: "800",
    color: "#111827",
    maxWidth: 220,
  },
  headerSub: {
    fontSize: 12,
    color: "#6B7280",
    marginTop: 2,
    fontWeight: "600",
  },
  closeBtn: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: "#F3F4F6",
    alignItems: "center",
    justifyContent: "center",
  },
  summaryBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "#F0FBF8",
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginBottom: 12,
  },
  summaryText: {
    fontSize: 12,
    color: "#3DBFA0",
    fontWeight: "600",
    flex: 1,
  },
  stepsList: {
    flex: 1,
  },
  stepsContent: {
    gap: 4,
    paddingBottom: 12,
  },
  stepItem: {
    flexDirection: "row",
    gap: 12,
    paddingVertical: 10,
  },
  stepConnector: {
    alignItems: "center",
    width: 32,
  },
  stepDot: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#F0FBF8",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1.5,
    borderColor: "#3DBFA0",
  },
  stepLine: {
    width: 1.5,
    flex: 1,
    backgroundColor: "#E5E7EB",
    marginTop: 4,
    marginBottom: -4,
  },
  stepContent: {
    flex: 1,
    paddingTop: 6,
  },
  stepInstruction: {
    fontSize: 13,
    fontWeight: "600",
    color: "#1F2937",
    lineHeight: 18,
    marginBottom: 3,
  },
  stepMeta: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  stepDist: {
    fontSize: 11,
    color: "#3DBFA0",
    fontWeight: "700",
  },
  stepSep: {
    fontSize: 11,
    color: "#9CA3AF",
  },
  stepDur: {
    fontSize: 11,
    color: "#9CA3AF",
    fontWeight: "500",
  },
  emptyState: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 40,
    gap: 12,
  },
  emptyText: {
    fontSize: 14,
    color: "#9CA3AF",
  },
});
