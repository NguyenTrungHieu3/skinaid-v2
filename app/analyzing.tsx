// app/analyzing.tsx
// Màn hình AI đang phân tích ảnh — gọi API POST /ai/analyze và navigate với analysis_id

import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect } from "react";
import { Alert, StatusBar, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import AnalyzingLoader from "../components/analysis/AnalyzingLoader";
import { Colors } from "../constants/colors";
import { analyzeWoundImage } from "../services/woundService";
import { getErrorMessage } from "../services/utils";

export default function AnalyzingScreen() {
  const insets = useSafeAreaInsets();
  const { uri } = useLocalSearchParams<{ uri: string }>();

  useEffect(() => {
    let cancelled = false;

    async function runAnalysis() {
      try {
        const result = await analyzeWoundImage(uri ?? "");
        if (cancelled) return;

        router.replace({
          pathname: "/analysis-result",
          params: {
            uri: uri ?? "",
            analysisId: result.analysis_id,
          },
        });
      } catch (error) {
        if (cancelled) return;
        const msg = getErrorMessage(error as any);
        Alert.alert(
          "Lỗi phân tích",
          msg,
          [
            { text: "Thử lại", onPress: runAnalysis },
            { text: "Hủy", style: "cancel", onPress: () => router.back() },
          ]
        );
      }
    }

    runAnalysis();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <View style={[styles.root, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />
      {/* AnalyzingLoader chạy animation trong khi await API */}
      <AnalyzingLoader duration={0} />
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: Colors.backgroundSecondary,
  },
});
