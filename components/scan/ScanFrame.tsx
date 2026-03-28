// components/scan/ScanFrame.tsx
import React, { useEffect, useRef } from "react";
import { Animated, Dimensions, StyleSheet, View } from "react-native";

const TEAL = "#3DBFA0";
const FRAME_SIZE = Dimensions.get("window").width * 0.65;
const CORNER_LENGTH = 36;
const CORNER_THICKNESS = 4;
const CORNER_RADIUS = 10;

export default function ScanFrame() {
  const pulse = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, {
          toValue: 1.04,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulse, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  return (
    <Animated.View style={[styles.frame, { transform: [{ scale: pulse }] }]}>
      {/* Top-left */}
      <View style={[styles.corner, styles.TL]}>
        <View style={[styles.hLine, { top: 0, left: 0 }]} />
        <View style={[styles.vLine, { top: 0, left: 0 }]} />
      </View>

      {/* Top-right */}
      <View style={[styles.corner, styles.TR]}>
        <View style={[styles.hLine, { top: 0, right: 0 }]} />
        <View style={[styles.vLine, { top: 0, right: 0 }]} />
      </View>

      {/* Bottom-left */}
      <View style={[styles.corner, styles.BL]}>
        <View style={[styles.hLine, { bottom: 0, left: 0 }]} />
        <View style={[styles.vLine, { bottom: 0, left: 0 }]} />
      </View>

      {/* Bottom-right */}
      <View style={[styles.corner, styles.BR]}>
        <View style={[styles.hLine, { bottom: 0, right: 0 }]} />
        <View style={[styles.vLine, { bottom: 0, right: 0 }]} />
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  frame: {
    width: FRAME_SIZE,
    height: FRAME_SIZE,
    position: "relative",
  },

  corner: {
    position: "absolute",
    width: CORNER_LENGTH,
    height: CORNER_LENGTH,
  },

  // Positions
  TL: { top: 0, left: 0 },
  TR: { top: 0, right: 0 },
  BL: { bottom: 0, left: 0 },
  BR: { bottom: 0, right: 0 },

  // Horizontal arm
  hLine: {
    position: "absolute",
    width: CORNER_LENGTH,
    height: CORNER_THICKNESS,
    backgroundColor: TEAL,
    borderRadius: CORNER_RADIUS,
  },

  // Vertical arm
  vLine: {
    position: "absolute",
    width: CORNER_THICKNESS,
    height: CORNER_LENGTH,
    backgroundColor: TEAL,
    borderRadius: CORNER_RADIUS,
  },
});
