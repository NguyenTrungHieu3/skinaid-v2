// components/image-check/FailState.tsx
import { Feather } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { ImageQualityIssue } from "../../constants/imageCheckTypes";

const TEAL = "#02A18D";

interface FailStateProps {
  issues: ImageQualityIssue[];
  onAutoFix: () => void;
  onSkip: () => void;
}

export default function FailState({ issues, onAutoFix, onSkip }: FailStateProps) {
  const hasFixableIssue = issues.some((i) => i.autoFixable);
  const allUnfixable = issues.every((i) => !i.autoFixable);

  return (
    <View style={styles.container}>
      {/* Error banner */}
      <View style={styles.errorBanner}>
        <Feather name="alert-triangle" size={18} color="#DC2626" />
        <Text style={styles.errorBannerText}>Phát hiện vấn đề chất lượng</Text>
      </View>

      {/* Issue list với description */}
      <View style={styles.issueList}>
        {issues.map((issue) => (
          <View key={issue.id} style={styles.issueCard}>
            {/* Header row */}
            <View style={styles.issueHeader}>
              <View style={styles.issueDot} />
              <Text style={styles.issueLabel}>{issue.label}</Text>
              {issue.autoFixable && (
                <View style={styles.fixableBadge}>
                  <Feather name="zap" size={10} color={TEAL} />
                  <Text style={styles.fixableBadgeText}>Có thể sửa</Text>
                </View>
              )}
            </View>
            {/* Description */}
            <Text style={styles.issueDesc}>{issue.description}</Text>
          </View>
        ))}
      </View>

      {/* Auto-fix button — chỉ hiện khi có issue có thể fix */}
      {hasFixableIssue && (
        <>
          <Text style={styles.hint}>
            {allUnfixable
              ? "Vui lòng chụp lại ảnh để được kết quả tốt nhất."
              : "Hệ thống có thể tự động sửa một số vấn đề trên."}
          </Text>

          <TouchableOpacity
            style={styles.autoFixBtn}
            onPress={onAutoFix}
            activeOpacity={0.85}
          >
            <Feather name="zap" size={16} color="#FFFFFF" style={{ marginRight: 8 }} />
            <Text style={styles.autoFixText}>Tự động sửa</Text>
          </TouchableOpacity>
        </>
      )}

      {/* Nếu tất cả không fix được → chỉ gợi ý chụp lại */}
      {allUnfixable && (
        <Text style={styles.hint}>
          Những lỗi trên cần chụp lại ảnh. Bạn vẫn có thể bỏ qua và tiếp tục.
        </Text>
      )}

      {/* Divider */}
      <View style={styles.dividerRow}>
        <View style={styles.dividerLine} />
        <Text style={styles.dividerText}>HOẶC</Text>
        <View style={styles.dividerLine} />
      </View>

      {/* Skip button */}
      <TouchableOpacity style={styles.skipBtn} onPress={onSkip} activeOpacity={0.8}>
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
    marginBottom: 16,
    gap: 8,
  },
  issueCard: {
    backgroundColor: "#FFF9F9",
    borderWidth: 1,
    borderColor: "#FDE8E8",
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    gap: 4,
  },
  issueHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  issueDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: "#DC2626",
  },
  issueLabel: {
    fontSize: 13,
    fontWeight: "700",
    color: "#991B1B",
    flex: 1,
  },
  fixableBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    backgroundColor: "#E6FAF7",
    borderWidth: 1,
    borderColor: "#A7F3D0",
    borderRadius: 20,
    paddingHorizontal: 7,
    paddingVertical: 2,
  },
  fixableBadgeText: {
    fontSize: 10,
    color: TEAL,
    fontWeight: "600",
  },
  issueDesc: {
    fontSize: 12,
    color: "#6B7280",
    lineHeight: 17,
    paddingLeft: 15,
  },
  hint: {
    fontSize: 13,
    fontWeight: "500",
    color: "#374151",
    marginBottom: 14,
    lineHeight: 19,
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
