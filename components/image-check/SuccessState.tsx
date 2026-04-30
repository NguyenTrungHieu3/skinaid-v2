// components/image-check/SuccessState.tsx
import { Feather } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

const TEAL = "#02A18D";

interface SuccessStateProps {
  onStartAnalysis: () => void;
}

export default function SuccessState({ onStartAnalysis }: SuccessStateProps) {
  return (
    <View style={styles.container}>
      {/* Success banner */}
      <View style={styles.successBanner}>
        <View style={styles.successIconWrap}>
          <Feather name="check-circle" size={20} color={TEAL} />
        </View>
        <View style={styles.successTextWrap}>
          <Text style={styles.successTitle}>Ảnh đạt chất lượng!</Text>
          <Text style={styles.successSub}>Sẵn sàng gửi tới AI để phân tích.</Text>
        </View>
      </View>

      {/* Quality check summary */}
      <View style={styles.checkList}>
        {[
          { icon: "maximize-2", label: "Kích thước ảnh phù hợp" },
          { icon: "crop",       label: "Tỉ lệ khung hình ổn định" },
          { icon: "file",       label: "Dung lượng file hợp lệ" },
          { icon: "eye",        label: "Độ sắc nét đạt yêu cầu" },
        ].map((item) => (
          <View key={item.icon} style={styles.checkRow}>
            <Feather name={item.icon as any} size={14} color={TEAL} />
            <Text style={styles.checkLabel}>{item.label}</Text>
            <Feather name="check" size={13} color={TEAL} style={{ marginLeft: "auto" }} />
          </View>
        ))}
      </View>

      {/* Start analysis button */}
      <TouchableOpacity
        style={styles.analyzeBtn}
        onPress={onStartAnalysis}
        activeOpacity={0.85}
      >
        <Feather name="activity" size={18} color="#FFFFFF" style={{ marginRight: 8 }} />
        <Text style={styles.analyzeBtnText}>Bắt đầu phân tích</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingTop: 20,
  },
  successBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    borderWidth: 1.5,
    borderColor: "#6EE7D0",
    backgroundColor: "#F0FDF9",
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  successIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "#CCFBF1",
    alignItems: "center",
    justifyContent: "center",
  },
  successTextWrap: {
    flex: 1,
    gap: 2,
  },
  successTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: "#065F46",
  },
  successSub: {
    fontSize: 12,
    color: "#0D9488",
  },
  checkList: {
    marginBottom: 20,
    borderWidth: 1,
    borderColor: "#D1FAE5",
    borderRadius: 10,
    overflow: "hidden",
  },
  checkRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#D1FAE5",
    backgroundColor: "#F0FDF9",
  },
  checkLabel: {
    fontSize: 13,
    color: "#065F46",
    fontWeight: "500",
  },
  analyzeBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: TEAL,
    borderRadius: 50,
    height: 52,
    shadowColor: TEAL,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 10,
    elevation: 5,
  },
  analyzeBtnText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
});
