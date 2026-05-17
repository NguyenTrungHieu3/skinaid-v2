// app/analysis-result.tsx
// Màn hình kết quả phân tích AI: tổng quan + danh sách vết thương để người dùng xác nhận
// TODO-2: Fetch getAnalysisDetail() → map SignificantWound → DetectedWound
// Logic LLM fallback nằm ở handleContinue()

import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  Image,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import AnalysisSummaryCard from "../components/analysis/AnalysisSummaryCard";
import WoundListItem from "../components/analysis/WoundListItem";
import {
  AnalysisResult,
  DetectedWound,
} from "../constants/analysisTypes";
import { Colors } from "../constants/colors";
import {
  AnalysisDetailResponse,
  SignificantWound,
  SubmitDetection,
  getAnalysisDetail,
  mapWoundLabel,
  mapWoundTypeId,
  resolveQuestionnaires,
} from "../services/woundService";
import { getErrorMessage } from "../services/utils";

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Map severity API → SeverityLevel FE */
function mapSeverityFE(severity: string): string {
  if (severity === 'severe') return 'NANG';
  if (severity === 'moderate') return 'TRUNG_BINH';
  return 'NHE';
}

/**
 * Map API SignificantWound[] → DetectedWound[]
 * boundingBox từ API là pixel tuyệt đối cần normalize về 0-1.
 * Nếu chưa biết kích thước ảnh (imgW=0) thì để nguyên px — normalize sau.
 */
function mapToDetectedWounds(
  wounds: SignificantWound[],
  imgW: number,
  imgH: number
): DetectedWound[] {
  return wounds.map((w, idx) => {
    const bb = w.bounding_box;
    // Nếu đã biết kích thước ảnh gốc, normalize về 0-1
    const boundingBox =
      imgW > 0 && imgH > 0
        ? {
            x: bb.x / imgW,
            y: bb.y / imgH,
            width: bb.width / imgW,
            height: bb.height / imgH,
          }
        : { x: 0, y: 0, width: 0, height: 0 }; // placeholder, update sau getSize
    const hasSeverity = !['psoriasis', 'fungal', 'acne'].includes(w.wound_type);
    return {
      id: w.detection_id,
      index: idx + 1,
      woundType: mapWoundLabel(w.wound_type),
      woundTypeId: mapWoundTypeId(w.wound_type),
      severity: hasSeverity ? (mapSeverityFE(w.severity) as any) : undefined,
      confidence: Math.round(w.confidence_score * 100),
      boundingBox,
      selected: true,
    };
  });
}

/** Build AnalysisResult để truyền cho AnalysisSummaryCard */
function buildAnalysisResult(
  detail: AnalysisDetailResponse,
  wounds: DetectedWound[],
  imageUri: string
): AnalysisResult {
  const avgConfidence =
    detail.significant_wounds.length > 0
      ? detail.significant_wounds.reduce((sum, w) => sum + w.confidence_score, 0) /
        detail.significant_wounds.length
      : 0;

  // Xác định loại chính: 1 loại duy nhất → tên đó, nhiều hơn → "Nhiều loại"
  const uniqueTypes = [...new Set(detail.significant_wounds.map((w) => w.wound_type))];
  const primaryWoundType =
    uniqueTypes.length === 1 ? mapWoundLabel(uniqueTypes[0]) : 'Nhiều loại';

  // Mức nghiêm trọng cao nhất
  const severityOrder: Record<string, number> = { severe: 3, moderate: 2, mild: 1 };
  const woundsWithSeverity = detail.significant_wounds.filter(
    (w) => !['psoriasis', 'fungal', 'acne'].includes(w.wound_type)
  );

  let mostSevereStr = 'Không phân loại';
  if (woundsWithSeverity.length > 0) {
    const highestSeverity = woundsWithSeverity.reduce(
      (prev, w) => ((severityOrder[w.severity] ?? 0) > (severityOrder[prev] ?? 0) ? w.severity : prev),
      'mild'
    );
    const severityLabel: Record<string, string> = { severe: 'Nặng', moderate: 'Trung bình', mild: 'Nhẹ' };
    mostSevereStr = severityLabel[highestSeverity] ?? highestSeverity;
  }

  return {
    imageUri,
    totalWounds: detail.total_detections,
    averageConfidence: Math.round(avgConfidence * 100 * 100) / 100,
    primaryWoundType,
    mostSevereWound: mostSevereStr,
    wounds,
  };
}

// ─── NoWoundDisclaimer ────────────────────────────────────────────────────────
function NoWoundDisclaimer() {
  const pulse = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 0.5, duration: 500, useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 1, duration: 500, useNativeDriver: true }),
      ])
    ).start();
  }, []);
  return (
    <Animated.View style={[styles.noWoundDisclaimerCard, { opacity: pulse }]}>
      <Feather name="alert-triangle" size={20} color="#B45309" />
      <View style={styles.noWoundDisclaimerBody}>
        <Text style={styles.noWoundDisclaimerTitle}>Lưu ý quan trọng</Text>
        <Text style={styles.noWoundDisclaimerText}>
          Phân tích AI chỉ mang tính tham khảo, không thay thế chẩn đoán lâm sàng.{' '}
          <Text style={styles.noWoundDisclaimerBold}>Luôn tham khảo bác sĩ</Text>
          {' '}nếu bạn có dấu hiệu bất thường.
        </Text>
      </View>
    </Animated.View>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function AnalysisResultScreen() {
  const insets = useSafeAreaInsets();
  const { uri, analysisId } = useLocalSearchParams<{ uri: string; analysisId: string }>();

  // ── State ───────────────────────────────────────────────────────
  const [analysisDetail, setAnalysisDetail] = useState<AnalysisDetailResponse | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [continuing, setContinuing] = useState(false);
  const [selectAll, setSelectAll] = useState<boolean | null>(null);
  // Kích thước ảnh gốc (pixel) — cần để normalize bounding box
  const [imgSize, setImgSize] = useState<{ w: number; h: number } | null>(null);

  // ── Scroll Animated value (parallax + header fade) ──────────────
  const scrollY = useRef(new Animated.Value(0)).current;

  // ── Fetch analysis detail ───────────────────────────────────────
  useEffect(() => {
    async function fetchDetail() {
      try {
        const detail = await getAnalysisDetail(analysisId);
        setAnalysisDetail(detail);

        if (uri) {
          // Lấy kích thước ảnh gốc để normalize bounding box pixel → 0-1
          Image.getSize(
            uri,
            (imgW, imgH) => {
              setImgSize({ w: imgW, h: imgH });
              const detectedWounds = mapToDetectedWounds(
                detail.significant_wounds,
                imgW,
                imgH
              );
              const analysisResult = buildAnalysisResult(detail, detectedWounds, uri);
              setResult(analysisResult);
              setLoading(false); // ← đúng chỗ: sau khi có đủ data
            },
            () => {
              // Fallback nếu không lấy được kích thước ảnh
              const detectedWounds = mapToDetectedWounds(detail.significant_wounds, 0, 0);
              const analysisResult = buildAnalysisResult(detail, detectedWounds, uri ?? '');
              setResult(analysisResult);
              setLoading(false);
            }
          );
        } else {
          const detectedWounds = mapToDetectedWounds(detail.significant_wounds, 0, 0);
          const analysisResult = buildAnalysisResult(detail, detectedWounds, '');
          setResult(analysisResult);
          setLoading(false);
        }
      } catch (err) {
        setLoading(false);
        Alert.alert(
          'Không thể tải kết quả',
          getErrorMessage(err as any),
          [{ text: 'Quay lại', onPress: () => router.back() }]
        );
      }
    }
    if (analysisId) {
      fetchDetail();
    } else {
      setLoading(false);
      Alert.alert('Lỗi', 'Thiếu ID phân tích', [{ text: 'Quay lại', onPress: () => router.back() }]);
    }
  }, [analysisId]);

  // ── Phân tích trạng thái selectAll ─────────────────────────────
  useEffect(() => {
    if (!result) return;
    const all = result.wounds.every((w) => w.selected);
    const none = result.wounds.every((w) => !w.selected);
    setSelectAll(all ? true : none ? false : null);
  }, [result?.wounds]);

  // ── Handler: toggle một vết ─────────────────────────────────────
  const handleToggleWound = useCallback((id: string) => {
    setResult((prev) =>
      prev
        ? {
            ...prev,
            wounds: prev.wounds.map((w) => (w.id === id ? { ...w, selected: !w.selected } : w)),
          }
        : prev
    );
  }, []);

  // ── Handler: chọn/bỏ chọn tất cả ───────────────────────────────
  const handleSelectAll = useCallback(() => {
    const newValue = selectAll !== true;
    setResult((prev) =>
      prev
        ? { ...prev, wounds: prev.wounds.map((w) => ({ ...w, selected: newValue })) }
        : prev
    );
  }, [selectAll]);

  // ── Handler: hủy bỏ ────────────────────────────────────────────
  const handleCancel = () => {
    router.replace("/(tabs)/home");
  };

  // ── Handler: tiếp tục — điểm quyết định LLM fallback ──────────
  const handleContinue = async () => {
    if (!result || !analysisDetail) return;

    const selectedWounds = analysisDetail.significant_wounds.filter((w) =>
      result.wounds.find((rw) => rw.id === w.detection_id && rw.selected)
    );
    if (selectedWounds.length === 0) return;

    const selectedDetectionsJson = JSON.stringify(selectedWounds);
    const detections: SubmitDetection[] = selectedWounds.map((w) => ({
      detection_id: w.detection_id,
      wound_type: w.wound_type,
      subtype: w.sub_type,
      severity: w.severity,
      confidence: w.confidence_score,
    }));

    setContinuing(true);
    try {
      // Thử resolve questionnaires — nếu thành công → luồng bình thường
      await resolveQuestionnaires(detections);

      router.push({
        pathname: '/wound-assessment' as any,
        params: {
          analysisId,
          selectedDetections: selectedDetectionsJson,
          imageUri: uri ?? '',
        },
      });
    } catch {
      // LLM/questionnaire không khả dụng → bỏ qua câu hỏi, dùng firstaid_snapshot
      router.replace({
        pathname: '/assessment-result' as any,
        params: {
          analysisId,
          selectedDetections: selectedDetectionsJson,
          synthesisJson: '',   // rỗng = fallback mode
          imageUri: uri ?? '',
        },
      });
    } finally {
      setContinuing(false);
    }
  };

  // ─── Loading state ────────────────────────────────────────────
  if (loading) {
    return (
      <View style={[styles.root, styles.centered, { paddingTop: insets.top }]}>
        <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />
        <ActivityIndicator size="large" color={Colors.primary} />
        <Text style={styles.loadingText}>Đang tải kết quả phân tích...</Text>
      </View>
    );
  }

  if (!result) return null;

  // ─── Empty state: Không phát hiện vết thương ──────────────────
  if (result.wounds.length === 0) {
    return (
      <View style={[styles.root, { paddingTop: insets.top }]}>
        <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />

        {/* Top Bar */}
        <View style={styles.topBar}>
          <TouchableOpacity
            style={styles.backBtn}
            onPress={() => router.replace('/(tabs)/home')}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Feather name="arrow-left" size={20} color={Colors.primary} />
          </TouchableOpacity>
          <Text style={styles.topBarTitle}>KẾT QUẢ PHÂN TÍCH</Text>
          <View style={styles.topBarSpacer} />
        </View>

        <Animated.ScrollView
          contentContainerStyle={[styles.noWoundScroll, { paddingBottom: insets.bottom + 32 }]}
          showsVerticalScrollIndicator={false}
        >
          {/* Medical disclaimer — luôn hiện đầu tiên */}
          <NoWoundDisclaimer />

          {/* Illustration */}
          <View style={styles.noWoundIllustration}>
            <View style={styles.noWoundIconRing}>
              <Feather name="search" size={48} color={Colors.primary} />
            </View>
            <Text style={styles.noWoundTitle}>Không phát hiện vết thương</Text>
            <Text style={styles.noWoundSubtitle}>
              AI không xác định được vết thương rõ ràng nào trong ảnh này. Hãy thử chụp lại với:
            </Text>

            {/* Tips */}
            <View style={styles.noWoundTips}>
              {[
                { icon: 'sun', text: 'Ánh sáng tốt, đủ sáng' },
                { icon: 'maximize-2', text: 'Gần, tập trung vào vùng vết thương' },
                { icon: 'camera', text: 'Giữ yên máy, tránh ảnh bị mờ' },
              ].map((tip) => (
                <View key={tip.icon} style={styles.noWoundTipRow}>
                  <View style={styles.noWoundTipIcon}>
                    <Feather name={tip.icon as any} size={14} color={Colors.primary} />
                  </View>
                  <Text style={styles.noWoundTipText}>{tip.text}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* Buttons */}
          <View style={styles.noWoundBtns}>
            {/* Chụp lại */}
            <TouchableOpacity
              style={styles.noWoundRetakeBtn}
              onPress={() => router.replace('/image-check' as any)}
              activeOpacity={0.85}
            >
              <LinearGradient
                colors={[Colors.primary, Colors.primaryDark]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.noWoundBtnGradient}
              >
                <Feather name="camera" size={18} color="#fff" />
                <Text style={styles.noWoundRetakeBtnText}>Chụp lại</Text>
              </LinearGradient>
            </TouchableOpacity>

            {/* Về trang chủ */}
            <TouchableOpacity
              style={styles.noWoundHomeBtn}
              onPress={() => router.replace('/(tabs)/home')}
              activeOpacity={0.8}
            >
              <Feather name="home" size={16} color={Colors.textLight} />
              <Text style={styles.noWoundHomeBtnText}>Về trang chủ</Text>
            </TouchableOpacity>
          </View>
        </Animated.ScrollView>
      </View>
    );
  }

  const selectedCount = result.wounds.filter((w) => w.selected).length;
  const totalCount = result.wounds.length;
  const canContinue = selectedCount > 0 && !continuing;


  return (
    <View style={[styles.root, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />

      {/* ── Top Bar ──────────────────────────────────────────────── */}
      <View style={styles.topBar}>
        <TouchableOpacity
          style={styles.backBtn}
          onPress={handleCancel}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Feather name="arrow-left" size={20} color={Colors.primary} />
        </TouchableOpacity>

        <Text style={styles.topBarTitle}>XÁC NHẬN VẾT THƯƠNG</Text>

        <View style={styles.topBarSpacer} />
      </View>

      {/* ── Scrollable content ───────────────────────────────────── */}
      <Animated.ScrollView
        style={styles.scroll}
        contentContainerStyle={[
          styles.scrollContent,
          { paddingBottom: 24 + insets.bottom },
        ]}
        showsVerticalScrollIndicator={false}
        onScroll={Animated.event(
          [{ nativeEvent: { contentOffset: { y: scrollY } } }],
          { useNativeDriver: true }
        )}
        scrollEventThrottle={16}
      >
        {/* Card tổng quan */}
        <AnalysisSummaryCard result={result} scrollY={scrollY} />

        {/* ── Section: Danh sách vết thương ───────────────────── */}
        <View style={styles.sectionWrapper}>
          {/* ── Section header area ──────────────────────────────── */}
          <View style={styles.sectionHeader}>
            {/* Row 1: Icon + Title + Count */}
            <View style={styles.sectionHeaderRow1}>
              <View style={styles.sectionTitleGroup}>
                <View style={styles.sectionIconBg}>
                  <Feather name="crosshair" size={16} color={Colors.primary} />
                </View>
                <View style={styles.sectionTitleTextArea}>
                  <Text style={styles.sectionTitle}>Danh sách vết thương</Text>
                  <Text style={styles.sectionSubtitle}>
                    Chọn các vết bạn muốn phân tích
                  </Text>
                </View>
              </View>
              {/* Count chip */}
              <View style={styles.countChip}>
                <Text style={styles.countChipSelected}>{selectedCount}</Text>
                <Text style={styles.countChipDivider}>/</Text>
                <Text style={styles.countChipTotal}>{totalCount}</Text>
              </View>
            </View>

            {/* Row 2: Hint + Select All */}
            <View style={styles.sectionHeaderRow2}>
              {/* Hint */}
              <View style={styles.hintRow}>
                <Feather name="info" size={11} color={Colors.textMuted} />
                <Text style={styles.hintText}>
                  Nhấn vào thẻ để chọn/bỏ chọn
                </Text>
              </View>

              {/* Select / Deselect all toggle */}
              <TouchableOpacity
                style={[
                  styles.selectAllBtn,
                  selectAll === true && styles.selectAllBtnActive,
                ]}
                onPress={handleSelectAll}
                activeOpacity={0.75}
              >
                <Feather
                  name={selectAll === true ? "check-square" : "square"}
                  size={13}
                  color={selectAll === true ? Colors.white : Colors.primary}
                />
                <Text
                  style={[
                    styles.selectAllBtnText,
                    selectAll === true && styles.selectAllBtnTextActive,
                  ]}
                >
                  {selectAll === true ? "Bỏ chọn tất cả" : "Chọn tất cả"}
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* ── Wound cards ─────────────────────────────────────── */}
          <View style={styles.woundList}>
            {result.wounds.map((wound: DetectedWound, index: number) => (
              <WoundListItem
                key={wound.id}
                wound={wound}
                imageUri={result.imageUri || undefined}
                onToggle={handleToggleWound}
                animDelay={index * 120}
              />
            ))}
          </View>
        </View>
      </Animated.ScrollView>

      {/* ── Bottom Action Bar ────────────────────────────────────── */}
      <View
        style={[
          styles.bottomBar,
          { paddingBottom: Math.max(insets.bottom, 16) },
        ]}
      >
        {/* Selection summary */}
        {canContinue && (
          <View style={styles.selectionSummary}>
            <View style={styles.selectionDot} />
            <Text style={styles.selectionSummaryText}>
              Đã chọn <Text style={styles.selectionCount}>{selectedCount}</Text> vết thương
            </Text>
          </View>
        )}

        {/* Buttons row */}
        <View style={styles.buttonRow}>
          {/* Hủy bỏ */}
          <TouchableOpacity
            style={styles.cancelBtn}
            onPress={handleCancel}
            activeOpacity={0.7}
          >
            <Feather name="x" size={16} color={Colors.textLight} style={{ marginRight: 6 }} />
            <Text style={styles.cancelBtnText}>Hủy bỏ</Text>
          </TouchableOpacity>

          {/* Tiếp tục */}
          <TouchableOpacity
            style={[
              styles.continueBtn,
              !canContinue && styles.continueBtnDisabled,
            ]}
            onPress={handleContinue}
            activeOpacity={canContinue ? 0.85 : 1}
            disabled={!canContinue}
          >
            {canContinue ? (
              <LinearGradient
                colors={[Colors.primary, Colors.primaryDark]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.continueBtnGradient}
              >
                {continuing ? (
                  <ActivityIndicator size="small" color={Colors.white} />
                ) : (
                  <>
                    <Text style={styles.continueBtnText}>Tiếp tục</Text>
                    <View style={styles.continueBtnBadge}>
                      <Text style={styles.continueBtnBadgeText}>{selectedCount}</Text>
                    </View>
                    <Feather name="arrow-right" size={16} color={Colors.white} />
                  </>
                )}
              </LinearGradient>
            ) : (
              <View style={styles.continueBtnGradient}>
                <Text style={[styles.continueBtnText, { color: Colors.textMuted }]}>
                  Chọn ít nhất 1 vết
                </Text>
              </View>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: Colors.backgroundSecondary,
  },
  centered: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    color: Colors.textLight,
    fontWeight: '500',
  },

  // ── TopBar ──────────────────────────────────────────────────────
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: Colors.backgroundSecondary,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 2,
  },
  topBarTitle: {
    flex: 1,
    textAlign: "center",
    fontSize: 13,
    fontWeight: "800",
    color: Colors.primary,
    letterSpacing: 1.5,
  },
  topBarSpacer: {
    width: 36,
  },

  // ── Scroll ──────────────────────────────────────────────────────
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 20,
  },

  // ── Wound Section ───────────────────────────────────────────────
  sectionWrapper: {
    marginTop: 20,
    marginHorizontal: 16,
    backgroundColor: Colors.white,
    borderRadius: 20,
    overflow: "hidden",
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 4,
    borderWidth: 1,
    borderColor: Colors.borderLight,
  },

  // ── Section Header ──────────────────────────────────────────────
  sectionHeader: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
    backgroundColor: Colors.white,
  },

  // Row 1: Icon + Title + Count chip
  sectionHeaderRow1: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  sectionTitleGroup: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    flex: 1,
  },
  sectionTitleTextArea: {
    flex: 1,
  },
  sectionIconBg: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: "rgba(2,161,141,0.10)",
    alignItems: "center",
    justifyContent: "center",
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.textPrimary,
    letterSpacing: 0.2,
  },
  sectionSubtitle: {
    fontSize: 11.5,
    color: Colors.textMuted,
    marginTop: 2,
  },

  // Count chip
  countChip: {
    flexDirection: "row",
    alignItems: "baseline",
    backgroundColor: "rgba(2,161,141,0.08)",
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    gap: 2,
    borderWidth: 1,
    borderColor: "rgba(2,161,141,0.15)",
    marginLeft: 10,
  },
  countChipSelected: {
    fontSize: 15,
    fontWeight: "800",
    color: Colors.primary,
  },
  countChipDivider: {
    fontSize: 12,
    fontWeight: "400",
    color: Colors.textMuted,
  },
  countChipTotal: {
    fontSize: 12,
    fontWeight: "600",
    color: Colors.textLight,
  },

  // Row 2: Hint + Select all
  sectionHeaderRow2: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },

  // Hint row
  hintRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    flex: 1,
  },
  hintText: {
    fontSize: 11,
    color: Colors.textMuted,
    fontStyle: "italic",
  },

  // Select All button
  selectAllBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: Colors.primary,
    backgroundColor: Colors.white,
  },
  selectAllBtnActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  selectAllBtnText: {
    fontSize: 11.5,
    fontWeight: "700",
    color: Colors.primary,
    letterSpacing: 0.2,
  },
  selectAllBtnTextActive: {
    color: Colors.white,
  },

  // List wrapper — inside the unified container
  woundList: {
    paddingVertical: 12,
    gap: 0,
  },

  // ── Bottom Bar ──────────────────────────────────────────────────
  bottomBar: {
    backgroundColor: Colors.white,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
    paddingHorizontal: 16,
    paddingTop: 12,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 12,
    gap: 10,
  },

  // Selection summary strip
  selectionSummary: {
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
    paddingHorizontal: 4,
  },
  selectionDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: Colors.primary,
  },
  selectionSummaryText: {
    fontSize: 12,
    color: Colors.textLight,
    fontWeight: "500",
  },
  selectionCount: {
    color: Colors.primary,
    fontWeight: "800",
  },

  buttonRow: {
    flexDirection: "row",
    gap: 10,
  },

  // Hủy bỏ
  cancelBtn: {
    flex: 1,
    height: 52,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: Colors.borderLight,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
  },
  cancelBtnText: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.textLight,
  },

  // Tiếp tục
  continueBtn: {
    flex: 2.2,
    height: 52,
    borderRadius: 14,
    overflow: "hidden",
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 12,
    elevation: 6,
  },
  continueBtnDisabled: {
    backgroundColor: Colors.backgroundTertiary,
    shadowOpacity: 0,
    elevation: 0,
  },
  continueBtnGradient: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingHorizontal: 16,
    borderRadius: 14,
    backgroundColor: Colors.backgroundTertiary,
  },
  continueBtnText: {
    fontSize: 14,
    fontWeight: "700",
    color: Colors.white,
    letterSpacing: 0.3,
  },
  continueBtnBadge: {
    backgroundColor: "rgba(255,255,255,0.25)",
    borderRadius: 10,
    minWidth: 22,
    height: 22,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 6,
  },
  continueBtnBadgeText: {
    color: Colors.white,
    fontSize: 11,
    fontWeight: "800",
  },

  // ── No Wound Empty State ──────────────────────────────────────────
  noWoundDisclaimerCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginHorizontal: 16,
    marginTop: 16,
    backgroundColor: '#FEF3C7',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: '#FCD34D',
  },
  noWoundDisclaimerBody: { flex: 1 },
  noWoundDisclaimerTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#92400E',
    marginBottom: 4,
  },
  noWoundDisclaimerText: {
    fontSize: 12,
    color: '#78350F',
    lineHeight: 18,
  },
  noWoundDisclaimerBold: {
    fontWeight: '700',
  },

  noWoundScroll: {
    paddingTop: 8,
    gap: 16,
  },
  noWoundIllustration: {
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingVertical: 24,
    gap: 12,
  },
  noWoundIconRing: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(2,161,141,0.10)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'rgba(2,161,141,0.20)',
    marginBottom: 8,
  },
  noWoundTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: Colors.textPrimary,
    textAlign: 'center',
  },
  noWoundSubtitle: {
    fontSize: 13.5,
    color: Colors.textLight,
    textAlign: 'center',
    lineHeight: 20,
  },
  noWoundTips: {
    width: '100%',
    gap: 10,
    marginTop: 8,
  },
  noWoundTipRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: Colors.white,
    borderRadius: 10,
    padding: 10,
    borderWidth: 1,
    borderColor: Colors.borderLight,
  },
  noWoundTipIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(2,161,141,0.10)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  noWoundTipText: {
    fontSize: 13,
    color: Colors.textPrimary,
    fontWeight: '500',
    flex: 1,
  },
  noWoundBtns: {
    paddingHorizontal: 16,
    gap: 10,
  },
  noWoundRetakeBtn: {
    height: 54,
    borderRadius: 14,
    overflow: 'hidden',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 6,
  },
  noWoundBtnGradient: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    borderRadius: 14,
  },
  noWoundRetakeBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.white,
    letterSpacing: 0.3,
  },
  noWoundHomeBtn: {
    height: 46,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: Colors.borderLight,
    backgroundColor: Colors.white,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  noWoundHomeBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textLight,
  },
});
