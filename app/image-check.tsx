// app/image-check.tsx
import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  ScrollView,
  StatusBar,
  StyleSheet,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import CheckTopBar from "../components/image-check/CheckTopBar";
import CropModal from "../components/image-check/CropModal";
import FailState from "../components/image-check/FailState";
import ImagePreview from "../components/image-check/ImagePreview";
import LoadingState from "../components/image-check/LoadingState";
import SuccessState from "../components/image-check/SuccessState";
import {
  CheckStatus,
  ImageQualityIssue,
} from "../constants/imageCheckTypes";
import {
  autoFixImage,
  checkImageQuality,
} from "../utils/imageQualityCheck";



export default function ImageCheckScreen() {
  // Nhận uri ảnh từ scan screen
  const { uri } = useLocalSearchParams<{ uri: string }>();

  const [currentUri, setCurrentUri] = useState(uri);
  const [status, setStatus] = useState<CheckStatus>("loading");
  const [issues, setIssues] = useState<ImageQualityIssue[]>([]);
  const [cropVisible, setCropVisible] = useState(false);

  // Sync khi uri thay đổi (lần đầu vào)
  useEffect(() => {
    if (uri) setCurrentUri(uri);
  }, [uri]);

  // Chạy check ngay khi vào màn hình hoặc sau crop
  useEffect(() => {
    if (!currentUri) return;
    runCheck(currentUri);
  }, [currentUri]);

  const runCheck = async (imageUri: string) => {
    setStatus("loading");
    const result = await checkImageQuality(imageUri);
    setStatus(result.passed ? "success" : "fail");
    setIssues(result.issues);
  };

  // ── Handlers ─────────────────────────────────────────────────
  const handleClose = () => router.replace("/(tabs)/home");

  const handleRetake = () => {
    // Quay lại màn hình scan
    router.back();
  };

  const handleZoomCrop = () => {
    setCropVisible(true);
  };

  const handleCropDone = (croppedUri: string) => {
    setCropVisible(false);
    setCurrentUri(croppedUri); // useEffect sẽ tự chạy lại check
  };

  const handleAutoFix = async () => {
    if (!currentUri) return;
    setStatus("loading");
    try {
      const { fixedUri } = await autoFixImage(currentUri, issues);
      // Cập nhật ảnh đã sửa → useEffect sẽ tự chạy lại check
      setCurrentUri(fixedUri);
    } catch {
      // Nếu fix thất bại → chạy lại check trên ảnh cũ
      await runCheck(currentUri);
    }
  };

  const handleSkip = () => {
    // Bỏ qua lỗi, vẫn tiếp tục phân tích
    navigateToAnalysis();
  };

  const handleStartAnalysis = () => {
    navigateToAnalysis();
  };

  const navigateToAnalysis = () => {
    // Điều hướng sang màn hình phân tích AI (loading → kết quả)
    router.push({
      pathname: "/analyzing",
      params: { uri: currentUri },
    });
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
        {currentUri ? (
          <ImagePreview uri={currentUri} showWaitOverlay={isLoading} />
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

      {/* Crop/Zoom Modal */}
      {currentUri ? (
        <CropModal
          visible={cropVisible}
          uri={currentUri}
          onDone={handleCropDone}
          onCancel={() => setCropVisible(false)}
        />
      ) : null}
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
