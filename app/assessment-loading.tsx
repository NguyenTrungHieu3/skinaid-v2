// app/assessment-loading.tsx
// Màn hình loading khi gọi LLM tạo phác đồ — thiết kế hiện đại, vòng % tương lai

import { router, useLocalSearchParams } from 'expo-router';
import React, { useEffect, useRef, useState } from 'react';
import {
  Alert,
  Animated,
  Easing,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Circle, Defs, LinearGradient, Stop } from 'react-native-svg';
import { Colors } from '../constants/colors';
import {
  SignificantWound,
  SubmitAnswer,
  SubmitDetection,
  submitWoundResponses,
} from '../services/woundService';
import { getErrorMessage } from '../services/utils';

const STEPS = [
  'Đang tổng hợp thông tin...',
  'Đánh giá mức độ rủi ro...',
  'Tạo phác đồ điều trị AI...',
  'Hoàn thiện báo cáo y khoa...',
];

const AnimatedCircle = Animated.createAnimatedComponent(Circle);
const SIZE = 240;
const STROKE_WIDTH = 10;
const RADIUS = (SIZE - STROKE_WIDTH) / 2;
const CIRCUMFERENCE = RADIUS * 2 * Math.PI;

export default function AssessmentLoadingScreen() {
  const insets = useSafeAreaInsets();
  const { analysisId, selectedDetections: rawDetections, answersJson, imageUri } =
    useLocalSearchParams<{
      analysisId: string;
      selectedDetections: string;
      answersJson: string;
      imageUri?: string;
    }>();

  const progressAnim = useRef(new Animated.Value(0)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const [percent, setPercent] = useState(0);
  const [stepIdx, setStepIdx] = useState(0);

  useEffect(() => {
    // 1. Progress tick up to 90% (waiting for API)
    Animated.timing(progressAnim, {
      toValue: 90,
      duration: 4000,
      easing: Easing.bezier(0.25, 0.46, 0.45, 0.94),
      useNativeDriver: false,
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

    // ── API call ──────────────────────────────────────────────────
    let cancelled = false;

    async function submitAndNavigate() {
      try {
        const selectedDetections: SignificantWound[] = JSON.parse(rawDetections ?? '[]');
        const answers: SubmitAnswer[] = JSON.parse(answersJson ?? '[]');

        const detections: SubmitDetection[] = selectedDetections.map((w) => ({
          detection_id: w.detection_id,
          wound_type: w.wound_type,
          subtype: w.sub_type,
          severity: w.severity,
          confidence: w.confidence_score,
        }));

        const submitResult = await submitWoundResponses({
          analysis_id: analysisId,
          detections,
          answers,
          forward_to_synthesis: true,
        });

        if (cancelled) return;

        // Animate progress to 100% quickly upon success
        Animated.timing(progressAnim, {
          toValue: 100,
          duration: 500,
          useNativeDriver: false,
        }).start();

        const llmFailed =
          !submitResult.syntheses ||
          submitResult.syntheses.length === 0 ||
          submitResult.syntheses.some((s) => s.error !== null || !s.structured_guidance);

        // Chờ animation % lên 100 rồi chuyển trang
        setTimeout(() => {
          if (cancelled) return;

          if (llmFailed) {
            router.replace({
              pathname: '/assessment-result' as any,
              params: {
                analysisId,
                selectedDetections: rawDetections,
                synthesisJson: '',
                imageUri: imageUri ?? '',
              },
            });
          } else {
            router.replace({
              pathname: '/assessment-result' as any,
              params: {
                analysisId,
                selectedDetections: rawDetections,
                synthesisJson: JSON.stringify(submitResult.syntheses),
                imageUri: imageUri ?? '',
              },
            });
          }
        }, 700);

      } catch (err) {
        if (cancelled) return;
        Alert.alert(
          'Không thể tải kết quả',
          getErrorMessage(err as any),
          [
            {
              text: 'Thử lại',
              onPress: submitAndNavigate,
            },
            {
              text: 'Dùng dữ liệu sẵn có',
              style: 'cancel',
              onPress: () => {
                router.replace({
                  pathname: '/assessment-result' as any,
                  params: {
                    analysisId,
                    selectedDetections: rawDetections,
                    synthesisJson: '',
                    imageUri: imageUri ?? '',
                  },
                });
              },
            },
          ]
        );
      }
    }

    submitAndNavigate();

    return () => {
      progressAnim.removeListener(listener);
      cancelled = true;
    };
  }, []);

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
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />

      <View style={styles.loaderWrapper}>
        <Animated.View style={[styles.pulseCircle, { transform: [{ scale: pulseAnim }] }]} />

        <Animated.View style={[styles.spinRingWrapper, { transform: [{ rotate }] }]}>
          <View style={styles.spinRingDot} />
        </Animated.View>

        <Svg width={SIZE} height={SIZE} style={styles.svg}>
          <Defs>
            <LinearGradient id="grad" x1="0" y1="0" x2="1" y2="1">
              <Stop offset="0" stopColor={Colors.primary} stopOpacity="1" />
              <Stop offset="1" stopColor="#02E0C4" stopOpacity="1" />
            </LinearGradient>
          </Defs>
          <Circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            stroke={`${Colors.primary}1A`}
            strokeWidth={STROKE_WIDTH}
            fill="none"
          />
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

        <View style={styles.centerContent}>
          <Text style={styles.percentText}>{percent}<Text style={styles.percentSymbol}>%</Text></Text>
          <Text style={styles.statusLabel}>GENERATING</Text>
        </View>
      </View>

      <Text style={styles.title}>Phác đồ sơ cứu AI</Text>
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
