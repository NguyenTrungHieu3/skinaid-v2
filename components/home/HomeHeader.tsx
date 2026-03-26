// components/home/HomeHeader.tsx
import { Feather } from "@expo/vector-icons";
import React from "react";
import { Image, StyleSheet, Text, TouchableOpacity, View } from "react-native";

const TEAL = "#3DBFA0";

interface HomeHeaderProps {
  onPressNotification?: () => void;
  onPressProfile?: () => void;
}

export default function HomeHeader({
  onPressNotification,
  onPressProfile,
}: HomeHeaderProps) {
  return (
    <View style={styles.container}>
      {/* Logo + App name */}
      <View style={styles.logoRow}>
        <View style={styles.scanFrame}>
          <View style={[styles.corner, styles.cornerTL]} />
          <View style={[styles.corner, styles.cornerTR]} />
          <View style={[styles.corner, styles.cornerBL]} />
          <View style={[styles.corner, styles.cornerBR]} />
          <Image
            source={require("../../assets/logo_1.png")}
            style={styles.logo}
            resizeMode="contain"
          />
        </View>
        
        <Text style={styles.appName}>
          <Text style={styles.light}>Skin</Text>
          <Text style={styles.bold}>Aid</Text>
        </Text>
      </View>

      {/* Right icons */}
      <View style={styles.actions}>
        <TouchableOpacity style={styles.iconBtn} onPress={onPressNotification}>
          <Feather name="bell" size={20} color="#4B5563" />
        </TouchableOpacity>
        <TouchableOpacity style={styles.avatarBtn} onPress={onPressProfile}>
          <Feather name="user" size={18} color="#4B5563" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const FRAME = 40;
const C = 10;
const T = 2;

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    paddingTop: 36,
    paddingBottom: 16,
    backgroundColor: "#FFFFFF",
  },
  logoRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  scanFrame: {
    width: FRAME,
    height: FRAME,
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  corner: { position: "absolute", width: C, height: C, borderColor: TEAL },
  cornerTL: {
    top: 0,
    left: 0,
    borderTopWidth: T,
    borderLeftWidth: T,
    borderTopLeftRadius: 2,
  },
  cornerTR: {
    top: 0,
    right: 0,
    borderTopWidth: T,
    borderRightWidth: T,
    borderTopRightRadius: 2,
  },
  cornerBL: {
    bottom: 0,
    left: 0,
    borderBottomWidth: T,
    borderLeftWidth: T,
    borderBottomLeftRadius: 2,
  },
  cornerBR: {
    bottom: 0,
    right: 0,
    borderBottomWidth: T,
    borderRightWidth: T,
    borderBottomRightRadius: 2,
  },
  logo: { width: 26, height: 26 },
  appName: { fontSize: 18 },
  light: { color: "#1A1A1A", fontWeight: "400" },
  bold: { color: "#1A1A1A", fontWeight: "700" },
  actions: { flexDirection: "row", alignItems: "center", gap: 10 },
  iconBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    alignItems: "center",
    justifyContent: "center",
  },
  avatarBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F9FAFB",
  },
});
