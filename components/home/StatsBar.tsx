// components/home/StatsBar.tsx
import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { APP_STATS } from "../../constants/woundTypes";

export default function StatsBar() {
  return (
    <View style={styles.container}>
      <StatItem value={APP_STATS.accuracy} label="ĐỘ CHÍNH XÁC AI" />
      <View style={styles.divider} />
      <StatItem value={APP_STATS.users} label="NGƯỜI DÙNG" />
      <View style={styles.divider} />
      <StatItem value={APP_STATS.woundTypes} label="PHÂN TÍCH" />
    </View>
  );
}

function StatItem({ value, label }: { value: string; label: string }) {
  return (
    <View style={styles.item}>
      <Text style={styles.value}>{value}</Text>
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    backgroundColor: "#FFFFFF",
    borderRadius: 0,
    paddingVertical: 18,
    paddingHorizontal: 8,
    alignItems: "center",
    justifyContent: "space-around",
    borderBottomWidth: 1,
    borderBottomColor: "#F1F5F9",
  },
  divider: {
    width: 1,
    height: 32,
    backgroundColor: "#E5E7EB",
  },
  item: {
    flex: 1,
    alignItems: "center",
    gap: 3,
  },
  value: {
    fontSize: 20,
    fontWeight: "800",
    color: "#1A1A1A",
  },
  label: {
    fontSize: 9,
    fontWeight: "600",
    color: "#9CA3AF",
    textAlign: "center",
    letterSpacing: 0.5,
  },
});
