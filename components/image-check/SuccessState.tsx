// components/image-check/SuccessState.tsx
import { Feather } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

const TEAL = "#3DBFA0";

interface SuccessStateProps {
  onStartAnalysis: () => void;
}

export default function SuccessState({ onStartAnalysis }: SuccessStateProps) {
  return (
    <View style={styles.container}>
      {/* Success banner */}
      <View style={styles.successBanner}>
        <Feather name="check" size={18} color={TEAL} />
        <Text style={styles.successText}>Image looks good!</Text>
      </View>

      <Text style={styles.hint}>Sẵn sàng gửi tới AI để phân tích.</Text>

      {/* Start analysis button */}
      <TouchableOpacity
        style={styles.analyzeBtn}
        onPress={onStartAnalysis}
        activeOpacity={0.85}
      >
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
    gap: 10,
    borderWidth: 1.5,
    borderColor: "#6EE7D0",
    backgroundColor: "#F0FDF9",
    borderRadius: 10,
    paddingVertical: 14,
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  successText: {
    fontSize: 15,
    fontWeight: "600",
    color: TEAL,
  },
  hint: {
    fontSize: 14,
    color: "#6B7280",
    marginBottom: 20,
  },
  analyzeBtn: {
    backgroundColor: TEAL,
    borderRadius: 50,
    height: 52,
    alignItems: "center",
    justifyContent: "center",
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
