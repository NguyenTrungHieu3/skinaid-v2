// components/profile/SettingsView.tsx
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

interface SettingsViewProps {
  onPressChangePassword: () => void;
}

export default function SettingsView({
  onPressChangePassword,
}: SettingsViewProps) {
  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <View style={styles.row}>
          <Text style={styles.rowLabel}>Đổi mật khẩu</Text>
          <TouchableOpacity
            style={styles.changeBtn}
            onPress={onPressChangePassword}
            activeOpacity={0.8}
          >
            <Text style={styles.changeBtnText}>Đổi</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
  },
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    overflow: "hidden",
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  rowLabel: {
    fontSize: 15,
    fontWeight: "600",
    color: "#1A1A1A",
  },
  changeBtn: {
    borderWidth: 1.5,
    borderColor: "#3DBFA0",
    borderRadius: 50,
    paddingVertical: 6,
    paddingHorizontal: 20,
  },
  changeBtnText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#3DBFA0",
  },
});
