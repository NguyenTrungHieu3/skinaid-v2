// components/home/HomeHeader.tsx
import { Feather } from "@expo/vector-icons";
import React from "react";
import { Image, StyleSheet, Text, TouchableOpacity, View } from "react-native";

interface HomeHeaderProps {
  onPressNotification?: () => void;
  onPressProfile?: () => void;
  unreadCount?: number;
}

export default function HomeHeader({
  onPressNotification,
  unreadCount = 0,
}: HomeHeaderProps) {
  return (
    <View style={styles.container}>
      {/* Logo + App Name */}
      <View style={styles.logoRow}>
        {/* <View style={styles.logoContainer}> */}
          <Image
            source={require("../../assets/logo.png")}
            style={styles.logo}
            resizeMode="contain"
          />
        {/* </View> */}
        <Text style={styles.appName}>Skin<Text style={styles.appNameAccent}>Aid</Text></Text>
      </View>

      {/* Notification Bell */}
      <TouchableOpacity style={styles.iconBtn} onPress={onPressNotification}>
        <Feather name="bell" size={20} color="#1A1A1A" />
        {unreadCount > 0 && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>
              {unreadCount > 99 ? '99+' : unreadCount}
            </Text>
          </View>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 12,
    backgroundColor: "transparent",
  },
  logoRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  // logoContainer: {
  //   width: 38,
  //   height: 38,
  //   borderRadius: 19,
  //   backgroundColor: "#FFFFFF",
  //   alignItems: "center",
  //   justifyContent: "center",
  //   shadowColor: "#000",
  //   shadowOffset: { width: 0, height: 1 },
  //   shadowOpacity: 0.1,
  //   shadowRadius: 4,
  //   elevation: 2,
  // },
  logo: { width: 36, height: 36 },
  appName: {
    fontSize: 20,
    fontWeight: "700",
    color: "#1A1A1A",
    letterSpacing: 0.3,
  },
  appNameAccent: {
    color: "#02A18D",
  },
  iconBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  badge: {
    position: "absolute",
    top: -2,
    right: -2,
    minWidth: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: "#FF3B30",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 4,
    borderWidth: 1.5,
    borderColor: "#FFFFFF",
  },
  badgeText: {
    color: "#FFFFFF",
    fontSize: 9,
    fontWeight: "800",
  },
});
