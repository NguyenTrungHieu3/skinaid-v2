// app/wound-assessment.tsx
// TODO-3: Fetch câu hỏi thực từ API resolveQuestionnaires()
// Câu hỏi hoàn toàn động theo API response — không hardcode số câu

import { Feather, Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router, useLocalSearchParams } from 'expo-router';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Animated,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Colors } from '../constants/colors';
import {
  ResolvedQuestionnaire,
  SignificantWound,
  SubmitDetection,
  resolveQuestionnaires,
} from '../services/woundService';
import { getErrorMessage } from '../services/utils';

// ─── Kiểu dữ liệu câu trả lời ───────────────────────────────────
// Map: question_id → answer_ids[]
type AnswerMap = Map<string, string[]>;

// ─── Màu accent theo loại vết thương (API wound_type) ───────────
const WOUND_ACCENT: Record<string, string> = {
  fungal: '#7B4FD5',
  abrasion: '#E05050',
  bruise: '#02A18D',
  burn: '#E87440',
  acne: '#3A7BD5',
  psoriasis: '#C04A3A',
};

function getAccentColor(wound_type: string): string {
  return WOUND_ACCENT[wound_type] ?? Colors.primary;
}

export default function WoundAssessmentScreen() {
  const insets = useSafeAreaInsets();
  const { analysisId, selectedDetections: rawDetections, imageUri } =
    useLocalSearchParams<{ analysisId: string; selectedDetections: string; imageUri?: string }>();

  // ── Parse selectedDetections ─────────────────────────────────────
  const selectedDetections: SignificantWound[] = useMemo(() => {
    try {
      return JSON.parse(rawDetections ?? '[]');
    } catch {
      return [];
    }
  }, [rawDetections]);

  // ── State ────────────────────────────────────────────────────────
  const [questionnaires, setQuestionnaires] = useState<ResolvedQuestionnaire[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeSetIndex, setActiveSetIndex] = useState(0);
  const [answers, setAnswers] = useState<AnswerMap>(new Map());

  // ── Animated progress bar ────────────────────────────────────────
  const progressAnim = useRef(new Animated.Value(0)).current;

  // ── Fetch questionnaires ─────────────────────────────────────────
  useEffect(() => {
    async function fetchQuestionnaires() {
      try {
        const detections: SubmitDetection[] = selectedDetections.map((w) => ({
          detection_id: w.detection_id,
          wound_type: w.wound_type,
          subtype: w.sub_type,
          severity: w.severity,
          confidence: w.confidence_score,
        }));

        const result = await resolveQuestionnaires(detections);
        setQuestionnaires(result);
      } catch (err) {
        Alert.alert(
          'Lỗi tải câu hỏi',
          getErrorMessage(err as any),
          [{ text: 'Quay lại', onPress: () => router.back() }]
        );
      } finally {
        setLoading(false);
      }
    }

    if (selectedDetections.length > 0) {
      fetchQuestionnaires();
    } else {
      setLoading(false);
    }
  }, []);

  // ── Tính toán tiến độ (hoàn toàn động theo API) ──────────────────
  const totalQuestions = useMemo(
    () => questionnaires.reduce((sum, q) => sum + q.questionnaire.questions.length, 0),
    [questionnaires]
  );

  const answeredCount = useMemo(
    () =>
      questionnaires.reduce(
        (sum, q) =>
          sum +
          q.questionnaire.questions.filter(
            (question) => (answers.get(question.question_id) ?? []).length > 0
          ).length,
        0
      ),
    [questionnaires, answers]
  );

  const progressPercent = totalQuestions > 0
    ? Math.round((answeredCount / totalQuestions) * 100)
    : 0;

  // Animate progress bar
  useEffect(() => {
    Animated.timing(progressAnim, {
      toValue: progressPercent / 100,
      duration: 400,
      useNativeDriver: false,
    }).start();
  }, [progressPercent]);

  // ── Kiểm tra tab nào đã hoàn thành ──────────────────────────────
  const isSetComplete = useCallback(
    (q: ResolvedQuestionnaire) =>
      q.questionnaire.questions.every(
        (question) => (answers.get(question.question_id) ?? []).length > 0
      ),
    [answers]
  );

  const allComplete = useMemo(
    () => questionnaires.length > 0 && questionnaires.every((q) => isSetComplete(q)),
    [questionnaires, isSetComplete]
  );

  // ── Handler: chọn / bỏ chọn một đáp án ─────────────────────────
  const handleSelectAnswer = useCallback(
    (questionId: string, answerId: string, isMultiple: boolean) => {
      setAnswers((prev) => {
        const next = new Map(prev);
        if (isMultiple) {
          const current = next.get(questionId) ?? [];
          next.set(
            questionId,
            current.includes(answerId)
              ? current.filter((id) => id !== answerId)
              : [...current, answerId]
          );
        } else {
          // radio: chỉ giữ 1
          next.set(questionId, [answerId]);
        }
        return next;
      });
    },
    []
  );

  // ── Handler: hoàn thành — navigate sang assessment-loading ───────
  const handleFinish = () => {
    const answersArray = Array.from(answers.entries()).map(([question_id, answer_ids]) => ({
      question_id,
      answer_ids,
    }));

    router.replace({
      pathname: '/assessment-loading' as any,
      params: {
        analysisId,
        selectedDetections: rawDetections,   // truyền nguyên (có firstaid_snapshot)
        answersJson: JSON.stringify(answersArray),
        imageUri: imageUri ?? '',
      },
    });
  };

  // ── Handler: hủy bỏ ─────────────────────────────────────────────
  const handleCancel = () => {
    router.replace('/(tabs)/home');
  };

  // ── Loading state ────────────────────────────────────────────────
  if (loading) {
    return (
      <View style={[styles.root, styles.centered, { paddingTop: insets.top }]}>
        <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />
        <ActivityIndicator size="large" color={Colors.primary} />
        <Text style={styles.loadingText}>Đang tải bộ câu hỏi...</Text>
      </View>
    );
  }

  // ── Empty state ─────────────────────────────────────────────────
  if (questionnaires.length === 0) {
    return (
      <View style={[styles.root, { paddingTop: insets.top }]}>
        <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />
        <View style={styles.emptyState}>
          <Ionicons name="alert-circle-outline" size={56} color={Colors.textMuted} />
          <Text style={styles.emptyTitle}>Không có câu hỏi nào cho vết thương này</Text>
          <TouchableOpacity style={styles.emptyBtn} onPress={() => router.back()}>
            <Text style={styles.emptyBtnText}>Quay lại</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const activeQ = questionnaires[activeSetIndex];
  const accentColor = activeQ ? getAccentColor(activeQ.wound_type) : Colors.primary;

  return (
    <View style={[styles.root, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />

      {/* ── Top Bar ──────────────────────────────────────────────── */}
      <View style={styles.topBar}>
        <TouchableOpacity
          style={styles.backBtn}
          onPress={() => router.back()}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Feather name="arrow-left" size={20} color={Colors.primary} />
        </TouchableOpacity>
        <Text style={styles.topBarTitle}>ĐÁNH GIÁ CHI TIẾT</Text>
        <View style={styles.topBarSpacer} />
      </View>

      {/* ── Progress Bar ─────────────────────────────────────────── */}
      <View style={styles.progressSection}>
        <View style={styles.progressLabelRow}>
          <Text style={styles.progressLabel}>
            Đã trả lời {answeredCount} / {totalQuestions} câu
          </Text>
          <Text style={styles.progressPercent}>{progressPercent}%</Text>
        </View>
        <View style={styles.progressTrack}>
          <Animated.View
            style={[
              styles.progressFill,
              {
                width: progressAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: ['0%', '100%'],
                }),
              },
            ]}
          >
            <LinearGradient
              colors={[Colors.primaryLight, Colors.primary]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={StyleSheet.absoluteFill}
            />
          </Animated.View>
        </View>
      </View>

      {/* ── Wound Type Tabs ──────────────────────────────────────── */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.tabsScroll}
        contentContainerStyle={styles.tabsContent}
      >
        {questionnaires.map((q, idx) => {
          const isActive = idx === activeSetIndex;
          const isDone = isSetComplete(q);
          const tabAccent = getAccentColor(q.wound_type);
          return (
            <TouchableOpacity
              key={`${q.wound_type}-${q.subtype ?? 'null'}`}
              style={[
                styles.tab,
                isActive && { backgroundColor: tabAccent, borderColor: tabAccent },
                !isActive && isDone && styles.tabDone,
              ]}
              onPress={() => setActiveSetIndex(idx)}
              activeOpacity={0.8}
            >
              {isDone && !isActive && (
                <Feather name="check" size={11} color={Colors.primary} style={{ marginRight: 4 }} />
              )}
              <Text
                style={[
                  styles.tabText,
                  isActive && styles.tabTextActive,
                  !isActive && isDone && styles.tabTextDone,
                ]}
              >
                {q.questionnaire.title}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      {/* ── Scrollable Content ───────────────────────────────────── */}
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[
          styles.scrollContent,
          { paddingBottom: 24 + insets.bottom },
        ]}
        showsVerticalScrollIndicator={false}
      >
        {/* Info Banner */}
        <View style={styles.infoBanner}>
          <View style={styles.infoBannerIcon}>
            <Ionicons name="information-circle" size={20} color={Colors.primary} />
          </View>
          <Text style={styles.infoBannerText}>
            Câu trả lời của bạn giúp hệ thống{' '}
            <Text style={styles.infoBannerBold}>
              đánh giá chính xác mức độ tổn thương
            </Text>{' '}
            và đề xuất hướng dẫn sơ cứu phù hợp nhất. Vui lòng trả lời
            trung thực theo tình trạng thực tế của vết thương.
          </Text>
        </View>

        {/* Set description */}
        {activeQ && (
          <View style={styles.setDescRow}>
            <View style={[styles.setDescDot, { backgroundColor: accentColor }]} />
            <Text style={styles.setDescText}>{activeQ.questionnaire.description}</Text>
          </View>
        )}

        {/* Questions — hoàn toàn động theo API response */}
        {activeQ?.questionnaire.questions.map((question, qIdx) => {
          const selectedIds = answers.get(question.question_id) ?? [];
          const isAnswered = selectedIds.length > 0;
          return (
            <View key={question.question_id} style={styles.questionCard}>
              {/* Question header */}
              <View style={styles.questionHeader}>
                <View
                  style={[
                    styles.questionNum,
                    isAnswered && { backgroundColor: accentColor },
                  ]}
                >
                  <Text
                    style={[
                      styles.questionNumText,
                      isAnswered && { color: Colors.white },
                    ]}
                  >
                    {qIdx + 1}
                  </Text>
                </View>
                <View style={styles.questionTitleArea}>
                  <Text style={styles.questionTitle}>{question.question_text}</Text>
                  <Text style={styles.questionHint}>
                    {question.is_multiple_choice
                      ? 'Chọn một hoặc nhiều đáp án'
                      : 'Chọn một đáp án'}
                  </Text>
                </View>
                {isAnswered && (
                  <View
                    style={[
                      styles.questionDoneTag,
                      { backgroundColor: accentColor + '18' },
                    ]}
                  >
                    <Feather name="check" size={11} color={accentColor} />
                  </View>
                )}
              </View>

              {/* Options — từ API answers[] */}
              <View style={styles.optionList}>
                {question.answers.map((ans, oIdx) => {
                  const isSelected = selectedIds.includes(ans.answer_id);
                  return (
                    <TouchableOpacity
                      key={ans.answer_id}
                      style={[
                        styles.optionRow,
                        isSelected && {
                          backgroundColor: accentColor + '12',
                          borderColor: accentColor,
                        },
                        oIdx < question.answers.length - 1 && styles.optionBorder,
                      ]}
                      onPress={() =>
                        handleSelectAnswer(
                          question.question_id,
                          ans.answer_id,
                          question.is_multiple_choice
                        )
                      }
                      activeOpacity={0.7}
                    >
                      <Text
                        style={[
                          styles.optionLabel,
                          isSelected && { color: accentColor, fontWeight: '600' },
                        ]}
                      >
                        {ans.answer_text}
                      </Text>
                      <View
                        style={[
                          question.is_multiple_choice ? styles.checkbox : styles.radio,
                          isSelected && {
                            borderColor: accentColor,
                            backgroundColor: accentColor,
                          },
                        ]}
                      >
                        {isSelected && (
                          <Feather
                            name={question.is_multiple_choice ? 'check' : 'circle'}
                            size={question.is_multiple_choice ? 11 : 8}
                            color={Colors.white}
                          />
                        )}
                      </View>
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>
          );
        })}

        {/* Navigation between sets */}
        {questionnaires.length > 1 && (
          <View style={styles.setNavRow}>
            {activeSetIndex > 0 && (
              <TouchableOpacity
                style={styles.setNavBtn}
                onPress={() => setActiveSetIndex((i) => i - 1)}
              >
                <Feather name="chevron-left" size={16} color={Colors.primary} />
                <Text style={styles.setNavText}>Nhóm trước</Text>
              </TouchableOpacity>
            )}
            <View style={{ flex: 1 }} />
            {activeSetIndex < questionnaires.length - 1 && (
              <TouchableOpacity
                style={[styles.setNavBtn, styles.setNavBtnRight]}
                onPress={() => setActiveSetIndex((i) => i + 1)}
              >
                <Text style={styles.setNavText}>Nhóm tiếp</Text>
                <Feather name="chevron-right" size={16} color={Colors.primary} />
              </TouchableOpacity>
            )}
          </View>
        )}
      </ScrollView>

      {/* ── Bottom Bar ───────────────────────────────────────────── */}
      <View style={[styles.bottomBar, { paddingBottom: Math.max(insets.bottom, 16) }]}>
        {/* Finish button */}
        <TouchableOpacity
          style={[styles.finishBtn, !allComplete && styles.finishBtnDisabled]}
          onPress={handleFinish}
          activeOpacity={allComplete ? 0.85 : 1}
          disabled={!allComplete}
        >
          {allComplete ? (
            <LinearGradient
              colors={[Colors.primaryLight, Colors.primaryDark]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.finishBtnGradient}
            >
              <Feather name="check-circle" size={18} color={Colors.white} />
              <Text style={styles.finishBtnText}>Hoàn thành</Text>
            </LinearGradient>
          ) : (
            <View style={styles.finishBtnGradient}>
              <Feather name="lock" size={16} color={Colors.textMuted} />
              <Text style={[styles.finishBtnText, { color: Colors.textMuted }]}>
                Trả lời đủ {totalQuestions} câu để hoàn thành
              </Text>
            </View>
          )}
        </TouchableOpacity>

        {/* Cancel */}
        <TouchableOpacity style={styles.cancelBtn} onPress={handleCancel}>
          <Text style={styles.cancelBtnText}>Hủy bỏ</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ─── Styles ──────────────────────────────────────────────────────
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

  // Empty state
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textLight,
    textAlign: 'center',
  },
  emptyBtn: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: Colors.primary,
    borderRadius: 12,
  },
  emptyBtnText: {
    color: Colors.white,
    fontWeight: '700',
    fontSize: 14,
  },

  // ── Top Bar ───────────────────────────────────────────────────
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
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
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 2,
  },
  topBarTitle: {
    flex: 1,
    textAlign: 'center',
    fontSize: 13,
    fontWeight: '800',
    color: Colors.primary,
    letterSpacing: 1.5,
  },
  topBarSpacer: { width: 36 },

  // ── Progress ──────────────────────────────────────────────────
  progressSection: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  progressLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  progressLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textLight,
  },
  progressPercent: {
    fontSize: 13,
    fontWeight: '800',
    color: Colors.primary,
  },
  progressTrack: {
    height: 8,
    backgroundColor: Colors.backgroundTertiary,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
    overflow: 'hidden',
  },

  // ── Tabs ──────────────────────────────────────────────────────
  tabsScroll: {
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
    flexGrow: 0,
  },
  tabsContent: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 8,
    flexDirection: 'row',
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: Colors.borderLight,
    backgroundColor: Colors.backgroundTertiary,
  },
  tabDone: {
    borderColor: Colors.primary + '40',
    backgroundColor: Colors.primary + '0D',
  },
  tabText: {
    fontSize: 12.5,
    fontWeight: '600',
    color: Colors.textLight,
  },
  tabTextActive: {
    color: Colors.white,
  },
  tabTextDone: {
    color: Colors.primary,
  },

  // ── Scroll ────────────────────────────────────────────────────
  scroll: { flex: 1 },
  scrollContent: {
    paddingTop: 16,
    paddingHorizontal: 16,
    gap: 14,
  },

  // Info Banner
  infoBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: '#EBF8F6',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#C0E8E2',
  },
  infoBannerIcon: { marginTop: 1 },
  infoBannerText: {
    flex: 1,
    fontSize: 12.5,
    color: Colors.textLight,
    lineHeight: 18,
  },
  infoBannerBold: {
    fontWeight: '700',
    color: Colors.primaryDark,
  },

  // Set description
  setDescRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    paddingHorizontal: 4,
  },
  setDescDot: {
    width: 4,
    height: '100%' as any,
    minHeight: 40,
    borderRadius: 2,
    marginTop: 2,
  },
  setDescText: {
    flex: 1,
    fontSize: 12,
    color: Colors.textMuted,
    lineHeight: 17,
    fontStyle: 'italic',
  },

  // Question Card
  questionCard: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 3,
    borderWidth: 1,
    borderColor: Colors.borderLight,
  },
  questionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  questionNum: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: Colors.backgroundTertiary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  questionNumText: {
    fontSize: 13,
    fontWeight: '800',
    color: Colors.textLight,
  },
  questionTitleArea: { flex: 1 },
  questionTitle: {
    fontSize: 14.5,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  questionHint: {
    fontSize: 11,
    color: Colors.textMuted,
    marginTop: 2,
    fontStyle: 'italic',
  },
  questionDoneTag: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },

  // Options
  optionList: { paddingVertical: 4 },
  optionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 13,
    backgroundColor: Colors.white,
    borderWidth: 0,
  },
  optionBorder: {
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  optionLabel: {
    flex: 1,
    fontSize: 13.5,
    color: Colors.textPrimary,
    paddingRight: 12,
    lineHeight: 19,
  },

  // Radio / Checkbox
  radio: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    borderColor: Colors.borderLight,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.white,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: Colors.borderLight,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.white,
  },

  // Set navigation
  setNavRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    marginBottom: 8,
  },
  setNavBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: Colors.primary,
    backgroundColor: Colors.white,
  },
  setNavBtnRight: {},
  setNavText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.primary,
  },

  // ── Bottom Bar ────────────────────────────────────────────────
  bottomBar: {
    backgroundColor: Colors.white,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
    paddingHorizontal: 16,
    paddingTop: 12,
    gap: 8,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 12,
  },

  finishBtn: {
    height: 52,
    borderRadius: 14,
    overflow: 'hidden',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 12,
    elevation: 6,
  },
  finishBtnDisabled: {
    shadowOpacity: 0,
    elevation: 0,
  },
  finishBtnGradient: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: 14,
    backgroundColor: Colors.backgroundTertiary,
  },
  finishBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.white,
    letterSpacing: 0.3,
  },

  cancelBtn: {
    height: 38,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelBtnText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.textMuted,
  },
});
