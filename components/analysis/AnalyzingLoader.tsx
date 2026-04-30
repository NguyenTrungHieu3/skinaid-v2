// components/analysis/AnalyzingLoader.tsx
// Màn hình loading khi AI đang phân tích ảnh — full screen overlay animation

import React, { useEffect, useRef } from "react";
import {
  Animated,
  Easing,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { Colors } from "../../constants/colors";

const STEPS = [
  "Tiền xử lý ảnh...",
  "Nhận diện vùng tổn thương...",
  "Phân loại vết thương...",
  "Đánh giá mức độ nghiêm trọng...",
  "Tổng hợp kết quả...",
];

interface Props {
  /** Tổng thời gian loading (ms) */
  duration?: number;
}

export default function AnalyzingLoader({ duration = 4000 }: Props) {
  // ── Vòng xoay scan ring ─────────────────────────────────────────
  const rotate = useRef(new Animated.Value(0)).current;
  const pulseOuter = useRef(new Animated.Value(1)).current;
  const pulseInner = useRef(new Animated.Value(0.85)).current;

  // ── Progress bar ────────────────────────────────────────────────
  const progress = useRef(new Animated.Value(0)).current;

  // ── Step text ───────────────────────────────────────────────────
  const [currentStep, setCurrentStep] = React.useState(0);
  const stepOpacity = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    // Spin
    Animated.loop(
      Animated.timing(rotate, {
        toValue: 1,
        duration: 1800,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();

    // Pulse outer
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseOuter, {
          toValue: 1.12,
          duration: 900,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseOuter, {
          toValue: 1,
          duration: 900,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    ).start();

    // Pulse inner (offset)
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseInner, {
          toValue: 1,
          duration: 900,
          delay: 300,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseInner, {
          toValue: 0.85,
          duration: 900,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    ).start();

    // Progress bar
    Animated.timing(progress, {
      toValue: 1,
      duration,
      easing: Easing.bezier(0.25, 0.46, 0.45, 0.94),
      useNativeDriver: false,
    }).start();

    // Step rotation
    const stepInterval = Math.floor(duration / STEPS.length);
    let step = 0;
    const interval = setInterval(() => {
      step++;
      if (step >= STEPS.length) {
        clearInterval(interval);
        return;
      }
      Animated.sequence([
        Animated.timing(stepOpacity, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(stepOpacity, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();
      setCurrentStep(step);
    }, stepInterval);

    return () => clearInterval(interval);
  }, []);

  const spinInterpolate = rotate.interpolate({
    inputRange: [0, 1],
    outputRange: ["0deg", "360deg"],
  });

  const progressWidth = progress.interpolate({
    inputRange: [0, 1],
    outputRange: ["0%", "100%"],
  });

  return (
    <View style={styles.container}>
      {/* ── Spinner ────────────────────────────────────────────── */}
      <View style={styles.spinnerContainer}>
        {/* Outer pulse ring */}
        <Animated.View
          style={[styles.pulseRingOuter, { transform: [{ scale: pulseOuter }] }]}
        />
        {/* Inner pulse ring */}
        <Animated.View
          style={[styles.pulseRingInner, { transform: [{ scale: pulseInner }] }]}
        />
        {/* Rotating border */}
        <Animated.View
          style={[
            styles.spinRing,
            { transform: [{ rotate: spinInterpolate }] },
          ]}
        />
        {/* Center circle with icon */}
        <View style={styles.centerCircle}>
          <Text style={styles.centerIcon}>🔬</Text>
        </View>
      </View>

      {/* ── Title ─────────────────────────────────────────────── */}
      <Text style={styles.title}>AI đang phân tích</Text>
      <Text style={styles.subtitle}>Vui lòng không tắt ứng dụng</Text>

      {/* ── Step text ─────────────────────────────────────────── */}
      <Animated.Text style={[styles.stepText, { opacity: stepOpacity }]}>
        {STEPS[currentStep]}
      </Animated.Text>

      {/* ── Progress bar ──────────────────────────────────────── */}
      <View style={styles.progressContainer}>
        <View style={styles.progressBg}>
          <Animated.View
            style={[styles.progressFill, { width: progressWidth }]}
          />
        </View>
        <Animated.Text style={styles.progressPct}>
          {/* Hiển thị % xấp xỉ */}
          {`${Math.round((currentStep / STEPS.length) * 100)}%`}
        </Animated.Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.backgroundSecondary,
    paddingHorizontal: 40,
    gap: 12,
  },
  // ── Spinner ─────────────────────────────────────────────────────
  spinnerContainer: {
    width: 120,
    height: 120,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 8,
  },
  pulseRingOuter: {
    position: "absolute",
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: `${Colors.primary}18`,
  },
  pulseRingInner: {
    position: "absolute",
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: `${Colors.primary}28`,
  },
  spinRing: {
    position: "absolute",
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 3,
    borderColor: Colors.primary,
    borderTopColor: "transparent",
    borderRightColor: `${Colors.primary}50`,
  },
  centerCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 10,
    elevation: 6,
  },
  centerIcon: {
    fontSize: 28,
  },
  // ── Text ────────────────────────────────────────────────────────
  title: {
    fontSize: 20,
    fontWeight: "800",
    color: Colors.textPrimary,
    letterSpacing: 0.3,
    marginTop: 8,
  },
  subtitle: {
    fontSize: 13,
    color: Colors.textMuted,
    fontWeight: "400",
  },
  stepText: {
    fontSize: 13,
    color: Colors.primary,
    fontWeight: "500",
    marginTop: 4,
  },
  // ── Progress ────────────────────────────────────────────────────
  progressContainer: {
    width: "100%",
    alignItems: "flex-end",
    gap: 6,
    marginTop: 8,
  },
  progressBg: {
    width: "100%",
    height: 6,
    backgroundColor: Colors.backgroundTertiary,
    borderRadius: 3,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    backgroundColor: Colors.primary,
    borderRadius: 3,
  },
  progressPct: {
    fontSize: 11,
    color: Colors.primary,
    fontWeight: "700",
  },
});
