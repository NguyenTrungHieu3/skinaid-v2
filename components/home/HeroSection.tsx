// components/home/HeroSection.tsx
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

const TEAL = "#3DBFA0";

interface HeroSectionProps {
  onPressScan: () => void;
}

export default function HeroSection({ onPressScan }: HeroSectionProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Phát hiện vết thương bằng AI</Text>
      <Text style={styles.subtitle}>Nhận diện 6 loại vết phổ biến</Text>
      <TouchableOpacity
        style={styles.button}
        onPress={onPressScan}
        activeOpacity={0.85}
      >
        <Text style={styles.buttonText}>Bắt đầu phân tích</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 28,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#1A1A1A",
    lineHeight: 32,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: "#6B7280",
    marginBottom: 16,
  },
  button: {
    backgroundColor: TEAL,
    alignSelf: "flex-start",
    paddingVertical: 11,
    paddingHorizontal: 22,
    borderRadius: 50,
    shadowColor: TEAL,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  buttonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
  },
});
