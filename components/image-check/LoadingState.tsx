// components/image-check/LoadingState.tsx
import React, { useEffect, useRef } from "react";
import { Animated, Easing, StyleSheet, Text, View } from "react-native";

const TEAL = "#3DBFA0";
const SIZE = 52;
const THICKNESS = 3;

export default function LoadingState() {
  const rotation = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.timing(rotation, {
        toValue: 1,
        duration: 1000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();
  }, []);

  const spin = rotation.interpolate({
    inputRange: [0, 1],
    outputRange: ["0deg", "360deg"],
  });

  return (
    <View style={styles.container}>
      {/* Dashed spinner */}
      <Animated.View
        style={[styles.spinner, { transform: [{ rotate: spin }] }]}
      >
        {/* Vẽ spinner bằng border + borderDashed không support trên RN,
            dùng 4 chấm xoay thay thế */}
        {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
          <View
            key={i}
            style={[
              styles.dot,
              {
                opacity: (i + 1) / 8,
                transform: [
                  { rotate: `${i * 45}deg` },
                  { translateY: -(SIZE / 2 - THICKNESS) },
                ],
              },
            ]}
          />
        ))}
      </Animated.View>

      <Text style={styles.label}>Đang đánh giá...</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    justifyContent: "center",
    paddingTop: 36,
    gap: 16,
  },
  spinner: {
    width: SIZE,
    height: SIZE,
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  dot: {
    position: "absolute",
    width: THICKNESS + 1,
    height: THICKNESS + 1,
    borderRadius: 99,
    backgroundColor: TEAL,
    top: SIZE / 2,
    left: SIZE / 2 - (THICKNESS + 1) / 2,
  },
  label: {
    fontSize: 15,
    fontWeight: "600",
    color: TEAL,
  },
});
