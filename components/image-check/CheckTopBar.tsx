// components/image-check/CheckTopBar.tsx
import { Feather, MaterialCommunityIcons } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

const TEAL = "#3DBFA0";

interface CheckTopBarProps {
  onClose: () => void;
  onZoomCrop?: () => void;
  onRetake?: () => void;
  showActions?: boolean; // ẩn zoom/retake lúc loading
}

export default function CheckTopBar({
  onClose,
  onZoomCrop,
  onRetake,
  showActions = false,
}: CheckTopBarProps) {
  return (
    <View style={styles.container}>
      {/* Left: Close (X) */}
      <TouchableOpacity
        style={styles.closeBtn}
        onPress={onClose}
        activeOpacity={0.8}
      >
        <Feather name="x" size={18} color="#6B7280" />
      </TouchableOpacity>

      {/* Center: SkinAid logo text */}
      <Text style={styles.logo}>
        <Text style={styles.logoLight}>Skin</Text>
        <Text style={styles.logoBold}>Aid</Text>
      </Text>

      {/* Right: zoom-crop + retake */}
      {showActions ? (
        <View style={styles.actions}>
          <TouchableOpacity
            style={styles.iconBtn}
            onPress={onZoomCrop}
            activeOpacity={0.75}
          >
            <MaterialCommunityIcons name="crop" size={20} color="#4B5563" />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.iconBtn}
            onPress={onRetake}
            activeOpacity={0.75}
          >
            <Feather name="rotate-cw" size={20} color="#4B5563" />
          </TouchableOpacity>
        </View>
      ) : (
        // Spacer để logo vẫn căn giữa khi không có actions
        <View style={styles.spacer} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingTop: 52,
    paddingBottom: 12,
    backgroundColor: "#FFFFFF",
  },
  closeBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "#F3F4F6",
    alignItems: "center",
    justifyContent: "center",
  },
  logo: {
    fontSize: 20,
  },
  logoLight: { color: "#1A1A1A", fontWeight: "400" },
  logoBold: { color: TEAL, fontWeight: "700" },
  actions: {
    flexDirection: "row",
    gap: 8,
  },
  iconBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "#F3F4F6",
    alignItems: "center",
    justifyContent: "center",
  },
  spacer: { width: 80 },
});
