// app/image-check.tsx
import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  View,
} from "react-native";

import CheckTopBar from "../components/image-check/CheckTopBar";
import FailState from "../components/image-check/FailState";
import ImagePreview from "../components/image-check/ImagePreview";
import LoadingState from "../components/image-check/LoadingState";
import SuccessState from "../components/image-check/SuccessState";
import {
  CheckStatus,
  ImageQualityIssue,
  MOCK_CHECK_DURATION,
  QUALITY_ISSUES,
} from "../constants/imageCheckTypes";

// ── Hàm giả lập kiểm tra chất lượng ảnh ──────────────────────
// TODO: thay bằng API call thật
async function mockCheckImageQuality(uri: string): Promise<{
  passed: boolean;
  issues: ImageQualityIssue[];
}> {
  await new Promise((res) => setTimeout(res, MOCK_CHECK_DURATION));

  // Giả lập: 50% pass, 50% fail — thay bằng logic thật
  const passed = Math.random() > 0.5;
  const issues = passed ? [] : [QUALITY_ISSUES.blur, QUALITY_ISSUES.unclear];

  return { passed, issues };
}

export default function ImageCheckScreen() {
  // Nhận uri ảnh từ scan screen
  const { uri } = useLocalSearchParams<{ uri: string }>();

  const [status, setStatus] = useState<CheckStatus>("loading");
  const [issues, setIssues] = useState<ImageQualityIssue[]>([]);

  // Chạy check ngay khi vào màn hình
  useEffect(() => {
    if (!uri) return;
    runCheck(uri);
  }, [uri]);

  const runCheck = async (imageUri: string) => {
    setStatus("loading");
    const result = await mockCheckImageQuality(imageUri);
    setStatus(result.passed ? "success" : "fail");
    setIssues(result.issues);
  };

  // ── Handlers ─────────────────────────────────────────────────
  const handleClose = () => router.back();

  const handleRetake = () => {
    // Quay lại màn hình scan
    router.back();
  };

  const handleZoomCrop = () => {
    // TODO: mở crop editor
    console.log("Zoom/crop:", uri);
  };

  const handleAutoFix = async () => {
    // Chạy lại check sau khi "tự động sửa"
    if (!uri) return;
    await runCheck(uri);
  };

  const handleSkip = () => {
    // Bỏ qua lỗi, vẫn tiếp tục phân tích
    navigateToAnalysis();
  };

  const handleStartAnalysis = () => {
    navigateToAnalysis();
  };

  const navigateToAnalysis = () => {
    // TODO: điều hướng sang màn hình kết quả AI
    // router.push({ pathname: "/analysis-result", params: { uri } });
    console.log("Start analysis with uri:", uri);
  };

  // ── Render ───────────────────────────────────────────────────
  const isLoading = status === "loading";

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />

      <CheckTopBar
        onClose={handleClose}
        onZoomCrop={handleZoomCrop}
        onRetake={handleRetake}
        showActions={!isLoading}
      />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        scrollEnabled={!isLoading}
      >
        {/* Ảnh preview — luôn hiển thị */}
        {uri ? (
          <ImagePreview uri={uri} showWaitOverlay={isLoading} />
        ) : (
          <View style={styles.noImage} />
        )}

        {/* State content */}
        {status === "loading" && <LoadingState />}
        {status === "fail" && (
          <FailState
            issues={issues}
            onAutoFix={handleAutoFix}
            onSkip={handleSkip}
          />
        )}
        {status === "success" && (
          <SuccessState onStartAnalysis={handleStartAnalysis} />
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: "#FFFFFF",
  },
  scroll: {
    flex: 1,
  },
  content: {
    paddingBottom: 40,
  },
  noImage: {
    height: 300,
    marginHorizontal: 16,
    borderRadius: 16,
    backgroundColor: "#F3F4F6",
  },
});
