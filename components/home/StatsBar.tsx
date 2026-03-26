// components/home/StatsBar.tsx
import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { APP_STATS } from "../../constants/woundTypes";

export default function StatsBar() {
  return (
    <View style={styles.container}>
      <StatItem label="Độ chính xác AI:" value={APP_STATS.accuracy} />
      <View style={styles.divider} />
      <StatItem label="Người dùng:" value={APP_STATS.users} />
      <View style={styles.divider} />
      <StatItem label="Vết thương phân tích:" value={APP_STATS.woundTypes} />
    </View>
  );
}

function StatItem({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.item}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    backgroundColor: "#F8FFFE",
    borderWidth: 1,
    borderColor: "#D1FAF0",
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 8,
    marginTop: 8,
    alignItems: "center",
    justifyContent: "space-around",
  },
  divider: {
    width: 1,
    height: 28,
    backgroundColor: "#D1FAF0",
  },
  item: {
    flex: 1,
    alignItems: "center",
    gap: 2,
  },
  label: {
    fontSize: 10,
    color: "#9CA3AF",
    textAlign: "center",
  },
  value: {
    fontSize: 13,
    fontWeight: "700",
    color: "#3DBFA0",
    textAlign: "center",
  },
});
