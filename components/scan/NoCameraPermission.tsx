// components/scan/NoCameraPermission.tsx
import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

interface NoCameraPermissionProps {
  onRequestPermission: () => void;
}

export default function NoCameraPermission({
  onRequestPermission,
}: NoCameraPermissionProps) {
  return (
    <View style={styles.container}>
      {/* Close button */}
      <TouchableOpacity style={styles.closeBtn} onPress={() => router.back()}>
        <Feather name="x" size={20} color="#FFFFFF" />
      </TouchableOpacity>

      <Feather name="camera-off" size={56} color="rgba(255,255,255,0.5)" />
      <Text style={styles.title}>Cần quyền truy cập camera</Text>
      <Text style={styles.desc}>
        SkinAid cần quyền camera để chụp ảnh vết thương và phân tích.
      </Text>

      <TouchableOpacity style={styles.btn} onPress={onRequestPermission}>
        <Text style={styles.btnText}>Cấp quyền camera</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#111",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 40,
    gap: 16,
  },
  closeBtn: {
    position: "absolute",
    top: 56,
    left: 20,
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: "rgba(255,255,255,0.15)",
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontSize: 20,
    fontWeight: "700",
    color: "#FFFFFF",
    textAlign: "center",
    marginTop: 8,
  },
  desc: {
    fontSize: 14,
    color: "rgba(255,255,255,0.6)",
    textAlign: "center",
    lineHeight: 22,
  },
  btn: {
    marginTop: 8,
    backgroundColor: "#3DBFA0",
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 50,
  },
  btnText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
});
