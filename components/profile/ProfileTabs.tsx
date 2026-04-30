// components/profile/ProfileTabs.tsx
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

export type ProfileTab = "info" | "settings";

interface ProfileTabsProps {
  activeTab: ProfileTab;
  onChangeTab: (tab: ProfileTab) => void;
}

export default function ProfileTabs({
  activeTab,
  onChangeTab,
}: ProfileTabsProps) {
  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={[styles.tab, activeTab === "info" && styles.tabActive]}
        onPress={() => onChangeTab("info")}
      >
        <Text
          style={[styles.tabText, activeTab === "info" && styles.tabTextActive]}
        >
          Thông tin cá nhân
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.tab, activeTab === "settings" && styles.tabActive]}
        onPress={() => onChangeTab("settings")}
      >
        <Text
          style={[
            styles.tabText,
            activeTab === "settings" && styles.tabTextActive,
          ]}
        >
          Cài đặt
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    marginHorizontal: 16,
    marginTop: 16,
    marginBottom: 16,
    borderWidth: 1.5,
    borderColor: "#02A18D",
    borderRadius: 50,
    overflow: "hidden",
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: "center",
    backgroundColor: "transparent",
    borderRadius: 50,
  },
  tabActive: {
    backgroundColor: "#02A18D",
  },
  tabText: {
    fontSize: 14,
    fontWeight: "500",
    color: "#9CA3AF",
  },
  tabTextActive: {
    color: "#FFFFFF",
    fontWeight: "600",
  },
});
