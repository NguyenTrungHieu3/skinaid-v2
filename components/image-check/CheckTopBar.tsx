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
      {/* Left */}
      <TouchableOpacity
        style={styles.closeBtn}
        onPress={onClose}
        activeOpacity={0.8}
      >
        <Feather name="x" size={18} color="#6B7280" />
      </TouchableOpacity>

      {/* Center - absolute */}
      <View style={styles.logoWrapper}>
        <Text style={styles.logo}>
          <Text style={styles.logoLight}>Skin</Text>
          <Text style={styles.logoBold}>Aid</Text>
        </Text>
      </View>

      {/* Right */}
      <View style={styles.actions}>
        {showActions && (
          <>
            <TouchableOpacity style={styles.iconBtn} onPress={onZoomCrop}>
              <MaterialCommunityIcons name="crop" size={20} color="#4B5563" />
            </TouchableOpacity>

            <TouchableOpacity style={styles.iconBtn} onPress={onRetake}>
              <Feather name="rotate-cw" size={20} color="#4B5563" />
            </TouchableOpacity>
          </>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingTop: 26,
    paddingBottom: 20,
    backgroundColor: "#FFFFFF",
  },

  // LEFT
  closeBtn: {
    // position: "absolute",

    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "#F3F4F6",
    alignItems: "center",
    justifyContent: "center",
  },

  // CENTER (QUAN TRỌNG)
  logoWrapper: {
    position: "absolute",
    left: 0,
    right: 0,
    alignItems: "center",
  },

  logo: {
    // position: "absolute",
    fontSize: 22,
  },

  logoLight: { color: "#1A1A1A", fontWeight: "700" },
  logoBold: { color: "#02A18D", fontWeight: "700" },

  // RIGHT
  actions: {
    // position: "absolute",
    marginLeft: "auto",
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
});
