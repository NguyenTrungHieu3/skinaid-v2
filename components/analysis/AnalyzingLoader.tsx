// components/analysis/AnalyzingLoader.tsx
// Màn hình loading khi AI đang phân tích ảnh — phong cách tương lai hiện đại

import React, { useEffect, useRef, useState } from "react";
import { Animated, Easing, StyleSheet, Text, View } from "react-native";
import Svg, { Circle, Defs, LinearGradient, Stop } from "react-native-svg";
import { Colors } from "../../constants/colors";

const STEPS = [
  "Khởi tạo AI Engine...",
  "Đang quét đặc trưng y khoa...",
  "Phân loại loại tổn thương...",
  "Đánh giá mức độ nghiêm trọng...",
  "Hoàn thiện kết quả phân tích...",
];

const AnimatedCircle = Animated.createAnimatedComponent(Circle);
const SIZE = 240;
const STROKE_WIDTH = 10;
const RADIUS = (SIZE - STROKE_WIDTH) / 2;
const CIRCUMFERENCE = RADIUS * 2 * Math.PI;

interface Props {
  duration?: number;
}

export default function AnalyzingLoader({ duration = 4500 }: Props) {
  // Vì truyền duration = 0 từ parent, ta sẽ override nếu nó quá ngắn
  const actualDuration = duration < 1000 ? 4500 : duration;

  const progressAnim = useRef(new Animated.Value(0)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const [percent, setPercent] = useState(0);
  const [stepIdx, setStepIdx] = useState(0);

  useEffect(() => {
    // 1. Progress tick up to 95% (remaining 5% will be conceptual or completed by parent unmount)
    Animated.timing(progressAnim, {
      toValue: 95,
      duration: actualDuration,
      easing: Easing.bezier(0.25, 0.46, 0.45, 0.94),
      useNativeDriver: false, // required for listener syncing and strokeDashoffset
    }).start();

    // 2. Rotate scanning ring
    Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 3500,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();

    // 3. Pulse effect for the background
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.05,
          duration: 1200,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1200,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    ).start();

    // 4. Update text based on progress
    const listener = progressAnim.addListener((state) => {
      setPercent(Math.round(state.value));
      let idx = Math.floor((state.value / 95) * STEPS.length);
      if (idx >= STEPS.length) idx = STEPS.length - 1;
      setStepIdx(idx);
    });

    return () => {
      progressAnim.removeListener(listener);
    };
  }, [actualDuration, progressAnim, rotateAnim, pulseAnim]);

  const strokeDashoffset = progressAnim.interpolate({
    inputRange: [0, 100],
    outputRange: [CIRCUMFERENCE, 0],
    extrapolate: "clamp",
  });

  const rotate = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ["0deg", "360deg"],
  });

  return (
    <View style={styles.container}>
      <View style={styles.loaderWrapper}>
        {/* Glow/Pulse background */}
        <Animated.View style={[styles.pulseCircle, { transform: [{ scale: pulseAnim }] }]} />

        {/* Outer Rotating dashes to look like a futuristic scanner */}
        <Animated.View style={[styles.spinRingWrapper, { transform: [{ rotate }] }]}>
          <View style={styles.spinRingDot} />
        </Animated.View>

        {/* SVG Progress Circle */}
        <Svg width={SIZE} height={SIZE} style={styles.svg}>
          <Defs>
            <LinearGradient id="grad" x1="0" y1="0" x2="1" y2="1">
              <Stop offset="0" stopColor={Colors.primary} stopOpacity="1" />
              <Stop offset="1" stopColor="#02E0C4" stopOpacity="1" />
            </LinearGradient>
          </Defs>
          {/* Track */}
          <Circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            stroke={`${Colors.primary}1A`}
            strokeWidth={STROKE_WIDTH}
            fill="none"
          />
          {/* Animated Fill */}
          <AnimatedCircle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            stroke="url(#grad)"
            strokeWidth={STROKE_WIDTH}
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="none"
          />
        </Svg>

        {/* Center Content */}
        <View style={styles.centerContent}>
          <Text style={styles.percentText}>{percent}<Text style={styles.percentSymbol}>%</Text></Text>
          <Text style={styles.statusLabel}>PROCESSING</Text>
        </View>
      </View>

      <Text style={styles.title}>Hệ thống AI đang phân tích</Text>
      <Text style={styles.stepText}>{STEPS[stepIdx]}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.backgroundSecondary,
    paddingHorizontal: 20,
  },
  loaderWrapper: {
    width: SIZE,
    height: SIZE,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 40,
  },
  pulseCircle: {
    position: "absolute",
    width: SIZE * 0.75,
    height: SIZE * 0.75,
    borderRadius: (SIZE * 0.75) / 2,
    backgroundColor: `${Colors.primary}15`,
  },
  spinRingWrapper: {
    position: "absolute",
    width: SIZE + 40,
    height: SIZE + 40,
    borderRadius: (SIZE + 40) / 2,
    borderWidth: 1.5,
    borderColor: `${Colors.primary}30`,
    borderStyle: "dashed",
    alignItems: "center",
  },
  spinRingDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: "#02E0C4",
    position: "absolute",
    top: -5,
    shadowColor: "#02E0C4",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 6,
    elevation: 4,
  },
  svg: {
    position: "absolute",
    transform: [{ rotate: "-90deg" }], // Bắt đầu vòng ở góc 12h
  },
  centerContent: {
    alignItems: "center",
    justifyContent: "center",
  },
  percentText: {
    fontSize: 56,
    fontWeight: "900",
    color: Colors.primary,
    fontVariant: ["tabular-nums"], // Số không bị nhảy giật
    letterSpacing: -1,
  },
  percentSymbol: {
    fontSize: 26,
    fontWeight: "700",
    color: Colors.primary,
  },
  statusLabel: {
    fontSize: 11,
    fontWeight: "800",
    color: Colors.textMuted,
    letterSpacing: 3,
    marginTop: -4,
  },
  title: {
    fontSize: 20,
    fontWeight: "800",
    color: Colors.textPrimary,
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  stepText: {
    fontSize: 14,
    color: Colors.primary,
    fontWeight: "600",
  },
});
