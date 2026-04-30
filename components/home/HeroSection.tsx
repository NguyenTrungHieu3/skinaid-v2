// components/home/HeroSection.tsx
import { Feather } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

interface HeroSectionProps {
  onPressScan: () => void;
}

export default function HeroSection({ onPressScan }: HeroSectionProps) {
  return (
    <View style={styles.container}>
      {/* AI POWERED Badge */}
      <View style={styles.badge}>
        <Text style={styles.badgeText}>AI POWERED</Text>
      </View>

      {/* Title */}
      <Text style={styles.title}>
        Phát hiện vết{"\n"}thương bằng AI
      </Text>

      {/* Subtitle */}
      <Text style={styles.subtitle}>
        Nhận diện 6 loại phổ biến với độ chính xác{"\n"}cao ngay trên điện thoại của bạn.
      </Text>

      {/* CTA Button */}
      <TouchableOpacity
        style={styles.button}
        onPress={onPressScan}
        activeOpacity={0.88}
      >
        <Feather
          name="maximize"
          size={16}
          color="#02A18D"
          style={{ marginRight: 8 }}
        />
        <Text style={styles.buttonText}>Bắt đầu phân tích</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 22,
    paddingTop: 16,
    paddingBottom: 32,
  },
  badge: {
    alignSelf: "flex-start",
    backgroundColor: "rgba(255, 255, 255, 0.2)",
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 5,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.35)",
  },
  badgeText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#FFFFFF",
    letterSpacing: 1.2,
  },
  title: {
    fontSize: 30,
    fontWeight: "800",
    color: "#FFFFFF",
    lineHeight: 38,
    marginBottom: 12,
    letterSpacing: 0.2,
  },
  subtitle: {
    fontSize: 14,
    color: "rgba(255, 255, 255, 0.82)",
    marginBottom: 28,
    lineHeight: 21,
  },
  button: {
    backgroundColor: "#FFFFFF",
    flexDirection: "row",
    alignSelf: "flex-start",
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 50,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 10,
    elevation: 5,
  },
  buttonText: {
    color: "#02A18D",
    fontSize: 15,
    fontWeight: "700",
  },
});
