// components/image-check/FailState.tsx
import { Feather } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { ImageQualityIssue } from "../../constants/imageCheckTypes";

interface FailStateProps {
  issues: ImageQualityIssue[];
  onAutoFix: () => void;
  onSkip: () => void;
}

export default function FailState({
  issues,
  onAutoFix,
  onSkip,
}: FailStateProps) {
  return (
    <View style={styles.container}>
      {/* Error banner */}
      <View style={styles.errorBanner}>
        <Feather name="alert-triangle" size={18} color="#DC2626" />
        <Text style={styles.errorBannerText}>Phát hiện vấn đề chất lượng</Text>
      </View>

      {/* Issue list */}
      <View style={styles.issueList}>
        {issues.map((issue) => (
          <View key={issue.id} style={styles.issueRow}>
            <Text style={styles.issueArrow}>↳</Text>
            <Text style={styles.issueText}>{issue.label}</Text>
          </View>
        ))}
      </View>

      <Text style={styles.hint}>Chúng tôi có thể thử sửa lỗi này tự động.</Text>

      {/* Auto-fix button */}
      <TouchableOpacity
        style={styles.autoFixBtn}
        onPress={onAutoFix}
        activeOpacity={0.85}
      >
        <Feather
          name="edit-2"
          size={16}
          color="#FFFFFF"
          style={{ marginRight: 8 }}
        />
        <Text style={styles.autoFixText}>Tự động sửa</Text>
      </TouchableOpacity>

      {/* Divider */}
      <View style={styles.dividerRow}>
        <View style={styles.dividerLine} />
        <Text style={styles.dividerText}>HOẶC</Text>
        <View style={styles.dividerLine} />
      </View>

      {/* Skip button */}
      <TouchableOpacity
        style={styles.skipBtn}
        onPress={onSkip}
        activeOpacity={0.8}
      >
        <Text style={styles.skipText}>Bỏ qua và tiếp tục</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingTop: 20,
  },
  errorBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    borderWidth: 1.5,
    borderColor: "#FCA5A5",
    backgroundColor: "#FEF2F2",
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 14,
  },
  errorBannerText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#DC2626",
  },
  issueList: {
    marginBottom: 12,
    paddingLeft: 4,
  },
  issueRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 4,
  },
  issueArrow: {
    fontSize: 13,
    color: "#DC2626",
    fontWeight: "600",
  },
  issueText: {
    fontSize: 13,
    color: "#DC2626",
  },
  hint: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1A1A1A",
    marginBottom: 16,
  },
  autoFixBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#7C3AED",
    borderRadius: 50,
    height: 52,
    marginBottom: 4,
    shadowColor: "#7C3AED",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  autoFixText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
  dividerRow: {
    flexDirection: "row",
    alignItems: "center",
    marginVertical: 12,
    gap: 10,
  },
  dividerLine: { flex: 1, height: 1, backgroundColor: "#E5E7EB" },
  dividerText: { fontSize: 12, color: "#9CA3AF", fontWeight: "500" },
  skipBtn: {
    height: 52,
    borderRadius: 50,
    backgroundColor: "#F3F4F6",
    alignItems: "center",
    justifyContent: "center",
  },
  skipText: {
    fontSize: 15,
    fontWeight: "600",
    color: "#374151",
  },
});
