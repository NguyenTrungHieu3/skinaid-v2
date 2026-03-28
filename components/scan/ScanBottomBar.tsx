// components/scan/ScanBottomBar.tsx
import { Feather } from "@expo/vector-icons";
import React, { useRef } from "react";
import { Animated, StyleSheet, TouchableOpacity, View } from "react-native";

interface ScanBottomBarProps {
  onCapture: () => void;
  onPickImage: () => void;
  isCapturing?: boolean;
}

export default function ScanBottomBar({
  onCapture,
  onPickImage,
  isCapturing = false,
}: ScanBottomBarProps) {
  const shutterScale = useRef(new Animated.Value(1)).current;

  const handleShutterPress = () => {
    // Animate shutter press
    Animated.sequence([
      Animated.timing(shutterScale, {
        toValue: 0.88,
        duration: 80,
        useNativeDriver: true,
      }),
      Animated.spring(shutterScale, {
        toValue: 1,
        friction: 4,
        useNativeDriver: true,
      }),
    ]).start();
    onCapture();
  };

  return (
    <View style={styles.container}>
      {/* Gallery button */}
      <TouchableOpacity
        style={styles.galleryBtn}
        onPress={onPickImage}
        activeOpacity={0.8}
      >
        <Feather name="image" size={22} color="#FFFFFF" />
      </TouchableOpacity>

      {/* Shutter button */}
      <Animated.View style={{ transform: [{ scale: shutterScale }] }}>
        <TouchableOpacity
          style={styles.shutter}
          onPress={handleShutterPress}
          activeOpacity={0.9}
          disabled={isCapturing}
        >
          <View style={styles.shutterInner} />
        </TouchableOpacity>
      </Animated.View>

      {/* Invisible spacer for centering */}
      <View style={styles.spacer} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 52,
    paddingBottom: 52,
    paddingTop: 20,
    zIndex: 10,
    // Subtle gradient-like dark overlay at bottom
    backgroundColor: "transparent",
  },

  // Gallery button — teal rounded square
  galleryBtn: {
    width: 52,
    height: 52,
    borderRadius: 14,
    backgroundColor: "#3DBFA0",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 4,
  },

  // Shutter outer ring
  shutter: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: "rgba(200,210,210,0.6)",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 3,
    borderColor: "rgba(255,255,255,0.5)",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 5,
  },

  // Shutter inner dot
  shutterInner: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: "rgba(200,230,225,0.85)",
  },

  spacer: {
    width: 52,
  },
});
