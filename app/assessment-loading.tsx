// app/assessment-loading.tsx
// TODO-4: Gọi submitWoundResponses() — xử lý LLM success và fallback
// Màn hình này chỉ được gọi khi LLM hoạt động bình thường.

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
import { Colors } from '../constants/colors';
import {
  SignificantWound,
  SubmitAnswer,
  SubmitDetection,
  submitWoundResponses,
} from '../services/woundService';
import { getErrorMessage } from '../services/utils';

const STEPS = [
  'Đang tổng hợp câu trả lời...',
  'Đánh giá mức độ tổn thương...',
  'Tạo hướng dẫn sơ cứu phù hợp...',
  'Hoàn thiện kết quả phân tích...',
];

export default function AssessmentLoadingScreen() {
  const insets = useSafeAreaInsets();
  const { analysisId, selectedDetections: rawDetections, answersJson, imageUri } =
    useLocalSearchParams<{
      analysisId: string;
      selectedDetections: string;
      answersJson: string;
      imageUri?: string;
    }>();

  const rotate = useRef(new Animated.Value(0)).current;
  const pulseOuter = useRef(new Animated.Value(1)).current;
  const pulseInner = useRef(new Animated.Value(0.85)).current;
  const progress = useRef(new Animated.Value(0)).current;
  const stepOpacity = useRef(new Animated.Value(1)).current;
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    // ── Animations ────────────────────────────────────────────────
    Animated.loop(
      Animated.timing(rotate, {
        toValue: 1,
        duration: 1500,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseOuter, {
          toValue: 1.18,
          duration: 880,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseOuter, {
          toValue: 1,
          duration: 880,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    ).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseInner, {
          toValue: 0.98,
          duration: 880,
          delay: 220,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseInner, {
          toValue: 0.85,
          duration: 880,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    ).start();

    // Progress bar — animate tới 90% trong khi chờ API
    // Sẽ complete sau khi API trả về
    Animated.timing(progress, {
      toValue: 0.9,
      duration: 3500,
      easing: Easing.bezier(0.25, 0.46, 0.45, 0.94),
      useNativeDriver: false,
    }).start();

    // Cycling step text
    const stepMs = 900;
    let step = 0;
    const interval = setInterval(() => {
      step = (step + 1) % STEPS.length;
      Animated.sequence([
        Animated.timing(stepOpacity, { toValue: 0, duration: 200, useNativeDriver: true }),
        Animated.timing(stepOpacity, { toValue: 1, duration: 200, useNativeDriver: true }),
      ]).start();
      setCurrentStep(step);
    }, stepMs);

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

        // Animate progress đến 100%
        Animated.timing(progress, {
          toValue: 1,
          duration: 400,
          useNativeDriver: false,
        }).start();

        // Kiểm tra LLM có thực sự trả về kết quả không
        const llmFailed =
          !submitResult.syntheses ||
          submitResult.syntheses.length === 0 ||
          submitResult.syntheses.some((s) => s.error !== null || !s.structured_guidance);

        // Delay nhỏ để animation hoàn tất
        setTimeout(() => {
          if (cancelled) return;

          if (llmFailed) {
            // Dùng firstaid_snapshot (đã có sẵn trong rawDetections)
            router.replace({
              pathname: '/assessment-result' as any,
              params: {
                analysisId,
                selectedDetections: rawDetections,
                synthesisJson: '',   // rỗng = fallback sang firstaid_snapshot
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
        }, 500);

      } catch (err) {
        if (cancelled) return;
        // Hard network error khi submit
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
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const spin = rotate.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });
  const progressWidth = progress.interpolate({
    inputRange: [0, 1],
    outputRange: ['0%', '100%'],
  });

  return (
    <View style={[styles.root, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />

      {/* Spinner */}
      <View style={styles.spinnerWrap}>
        <Animated.View style={[styles.pulseOuter, { transform: [{ scale: pulseOuter }] }]} />
        <Animated.View style={[styles.pulseInner, { transform: [{ scale: pulseInner }] }]} />
        <Animated.View style={[styles.spinRing, { transform: [{ rotate: spin }] }]} />
        <View style={styles.centerCircle}>
          <Text style={styles.centerEmoji}>🧬</Text>
        </View>
      </View>

      {/* Tiêu đề */}
      <Text style={styles.title}>AI đang tổng hợp kết quả</Text>
      <Text style={styles.subtitle}>Vui lòng không tắt ứng dụng</Text>

      {/* Bước hiện tại */}
      <Animated.Text style={[styles.stepText, { opacity: stepOpacity }]}>
        {STEPS[currentStep]}
      </Animated.Text>

      {/* Thanh progress */}
      <View style={styles.progressWrap}>
        <View style={styles.progressTrack}>
          <Animated.View style={[styles.progressFill, { width: progressWidth }]} />
        </View>
      </View>

      {/* Chấm bước */}
      <View style={styles.stepDots}>
        {STEPS.map((_, idx) => (
          <View
            key={idx}
            style={[styles.stepDot, idx <= currentStep && styles.stepDotActive]}
          />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
    gap: 18,
  },
  spinnerWrap: {
    width: 150,
    height: 150,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  pulseOuter: {
    position: 'absolute',
    width: 148,
    height: 148,
    borderRadius: 74,
    backgroundColor: `${Colors.primary}12`,
  },
  pulseInner: {
    position: 'absolute',
    width: 114,
    height: 114,
    borderRadius: 57,
    backgroundColor: `${Colors.primary}20`,
  },
  spinRing: {
    position: 'absolute',
    width: 86,
    height: 86,
    borderRadius: 43,
    borderWidth: 3.5,
    borderColor: Colors.primary,
    borderTopColor: 'transparent',
    borderRightColor: `${Colors.primary}50`,
  },
  centerCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: Colors.white,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.22,
    shadowRadius: 12,
    elevation: 7,
  },
  centerEmoji: { fontSize: 28 },

  title: {
    fontSize: 22,
    fontWeight: '800',
    color: Colors.textPrimary,
    letterSpacing: 0.2,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 13,
    color: Colors.textMuted,
    marginTop: -10,
  },
  stepText: {
    fontSize: 14,
    color: Colors.primary,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: -6,
  },

  progressWrap: { width: '100%' },
  progressTrack: {
    width: '100%',
    height: 7,
    backgroundColor: Colors.backgroundTertiary,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: Colors.primary,
    borderRadius: 4,
  },

  stepDots: {
    flexDirection: 'row',
    gap: 8,
    marginTop: -6,
  },
  stepDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.backgroundTertiary,
  },
  stepDotActive: {
    backgroundColor: Colors.primary,
    transform: [{ scale: 1.2 }],
  },
});
