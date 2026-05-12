import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
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
import {
  AnalysisHistoryDetail,
  BoundingBox,
  ChatMessage,
  FirstAidSection,
  WoundDetail,
} from "../constants/analysisTypes";
import { Colors } from "../constants/colors";
import { getAnalysisDetail, resolveQuestionnaires, mapWoundLabel, mapSeverityColor, mapSeverityLabel } from "../services/woundService";
import { chatbotService } from "../services/chatbotService";
import { useAuth } from "../context/AuthContext";

// In-memory cache cho trang chi tiết để chống load lại
const globalDetailCache: Record<string, AnalysisHistoryDetail> = {};

// ─── Màu cứng cho section first aid (data-driven, không phải theme) ───────
const SECTION_COLORS = {
  'Sơ cứu ngay': {
    iconBg: '#F0FDF4',
    iconColor: '#16A34A',
    stepNumberColor: '#16A34A',
    stepNumberBg: '#DCFCE7',
    stepNumberBorder: '#86EFAC',
    gradientBg: '#F0FDF4',
    headerBg: '#DCFCE7',
    accentLine: '#16A34A',
    icon: '!',
    tag: 'KHẨN CẤP',
  },
  'Nên làm': {
    iconBg: '#EFF6FF',
    iconColor: '#2563EB',
    stepNumberColor: '#2563EB',
    stepNumberBg: '#DBEAFE',
    stepNumberBorder: '#93C5FD',
    gradientBg: '#EFF6FF',
    headerBg: '#DBEAFE',
    accentLine: '#2563EB',
    icon: '✓',
    tag: 'KHUYẾN NGHỊ',
  },
  'Không nên làm': {
    iconBg: '#FFF7ED',
    iconColor: '#F97316',
    stepNumberColor: '#F97316',
    stepNumberBg: '#FFF7ED',
    stepNumberBorder: '#FDBA74',
    gradientBg: '#FFF7ED',
    headerBg: '#FED7AA',
    accentLine: '#F97316',
    icon: '✕',
    tag: 'CẢNH BÁO',
  },
} as const;

// ─── Component: Medical Scan Card (ảnh + loại + accuracy + severity) ──────
function WoundScanCard({ wound }: { wound: WoundDetail }) {
  const [imgSize, setImgSize] = useState({ width: 0, height: 0 });

  return (
    <View style={styles.scanCard}>
      {/* ── Zone ảnh với bounding box ── */}
      <View
        style={styles.scanImageZone}
        onLayout={(e) =>
          setImgSize({
            width: e.nativeEvent.layout.width,
            height: e.nativeEvent.layout.height,
          })
        }
      >
        {/* Render ảnh hoặc Placeholder */}
        {wound.imageUri ? (
          <Image source={{ uri: wound.imageUri }} style={{ width: '100%', height: '100%' }} />
        ) : (
          <View style={styles.scanImagePlaceholder}>
            {/* Lưới y tế giả để trông như ảnh scan */}
            <View style={styles.scanGrid}>
              {[0.25, 0.5, 0.75].map((v) => (
                <View key={v} style={[styles.scanGridLineH, { top: `${v * 100}%` }]} />
              ))}
              {[0.33, 0.66].map((v) => (
                <View key={v} style={[styles.scanGridLineV, { left: `${v * 100}%` }]} />
              ))}
            </View>
            <Feather name="aperture" size={40} color="rgba(2,161,141,0.25)" />
            <Text style={styles.scanPlaceholderText}>Ảnh phân tích</Text>
          </View>
        )}

        {/* Bounding box overlay */}
        {imgSize.width > 0 && imgSize.height > 0 && (
          <View
            style={{
              position: 'absolute',
              left: wound.boundingBox.x * imgSize.width,
              top: wound.boundingBox.y * imgSize.height,
              width: wound.boundingBox.width * imgSize.width,
              height: wound.boundingBox.height * imgSize.height,
              borderColor: Colors.primary,
              borderWidth: 2,
              borderRadius: 4,
            }}
          >
            {/* Góc bo teal */}
            <View style={[styles.boxCorner, styles.boxCornerTL]} />
            <View style={[styles.boxCorner, styles.boxCornerTR]} />
            <View style={[styles.boxCorner, styles.boxCornerBL]} />
            <View style={[styles.boxCorner, styles.boxCornerBR]} />
          </View>
        )}

        {/* Chip AI góc trên phải */}
        <View style={styles.aiChip}>
          <View style={styles.aiChipDot} />
          <Text style={styles.aiChipText}>AI Detection</Text>
        </View>

        {/* Gradient overlay + tên loại tổn thương ở đáy ảnh */}
        <LinearGradient
          colors={['transparent', 'rgba(0,0,0,0.72)']}
          style={styles.scanGradient}
        >
          <Text style={styles.scanWoundType}>LOẠI TỔN THƯƠNG</Text>
          <Text style={styles.scanWoundLabel}>{wound.label}</Text>
        </LinearGradient>
      </View>

      {/* ── Info panel phía dưới ── */}
      <View style={styles.scanInfoPanel}>
        {/* Accuracy */}
        <View style={styles.scanInfoLeft}>
          <Text style={styles.scanInfoCaption}>ĐỘ TIN CẬY</Text>
          <View style={styles.scanAccuracyRow}>
            <Text style={styles.scanAccuracyValue}>{wound.accuracy}%</Text>
          </View>
          <View style={styles.scanAccuracyTrack}>
            <View style={[styles.scanAccuracyFill, { width: `${wound.accuracy}%` }]} />
          </View>
        </View>

        {/* Divider */}
        <View style={styles.scanInfoDivider} />

        {/* Severity (hoặc N/A nếu không có) */}
        <View style={styles.scanInfoRight}>
          <Text style={styles.scanInfoCaption}>MỨC ĐỘ</Text>
          {wound.hasSeverity && wound.severity ? (
            <>
              <View
                style={[
                  styles.scanSeverityBadge,
                  { borderColor: wound.severityColor ?? Colors.primary },
                ]}
              >
                <View
                  style={[
                    styles.scanSeverityDot,
                    { backgroundColor: wound.severityColor ?? Colors.primary },
                  ]}
                />
                <Text
                  style={[
                    styles.scanSeverityText,
                    { color: wound.severityColor ?? Colors.primary },
                  ]}
                >
                  {wound.severity}
                </Text>
              </View>
              <Text style={styles.scanSeverityNote}>Cần theo dõi</Text>
            </>
          ) : (
            <>
              <Text style={styles.scanNoSeverityText}>Không
phân loại</Text>
              <Text style={styles.scanSeverityNote}>Bệnh mãn tính</Text>
            </>
          )}
        </View>
      </View>
    </View>
  );
}

// ─── Component: First Aid Section ───────────────────────────────
function FirstAidSectionCard({ section }: { section: FirstAidSection }) {
  const cfg = SECTION_COLORS[section.title];
  return (
    <View style={styles.firstAidGroup}>
      {/* ── Header có màu nền tương ứng ── */}
      <View style={[styles.firstAidHeader, { backgroundColor: cfg.headerBg }]}>
        {/* Icon tràn */}
        <View style={[styles.firstAidIconBadge, { backgroundColor: cfg.iconColor }]}>
          <Text style={styles.firstAidIconChar}>{cfg.icon}</Text>
        </View>
        {/* Tiêu đề và tag */}
        <View style={styles.firstAidHeaderText}>
          <Text style={[styles.firstAidTitle, { color: cfg.iconColor }]}>
            {section.title}
          </Text>
          <Text style={[styles.firstAidTag, { color: cfg.iconColor }]}>{cfg.tag}</Text>
        </View>
        {/* Badge số bước */}
        <View style={[styles.firstAidStepCount, { backgroundColor: cfg.iconColor }]}>
          <Text style={styles.firstAidStepCountText}>{section.steps.length}</Text>
          <Text style={styles.firstAidStepCountLabel}> BƯỚC</Text>
        </View>
      </View>

      {/* ── Timeline steps ── */}
      <View style={styles.timelineContainer}>
        {section.steps.map((step, idx) => {
          const isLast = idx === section.steps.length - 1;
          return (
            <View key={idx} style={styles.timelineRow}>
              {/* Cột trái: số + đường nối */}
              <View style={styles.timelineLeft}>
                <View
                  style={[
                    styles.timelineCircle,
                    {
                      backgroundColor: cfg.stepNumberBg,
                      borderColor: cfg.stepNumberBorder,
                    },
                  ]}
                >
                  <Text style={[styles.timelineNumber, { color: cfg.stepNumberColor }]}>
                    {idx + 1}
                  </Text>
                </View>
                {/* Đường nối dọc (chỉ hiện nếu không phải bước cuối) */}
                {!isLast && (
                  <View
                    style={[styles.timelineLine, { backgroundColor: cfg.stepNumberBorder }]}
                  />
                )}
              </View>

              {/* Cột phải: nội dung */}
              <View style={[styles.timelineContent, isLast && styles.timelineContentLast]}>
                <Text style={styles.timelineText}>{step.content}</Text>
              </View>
            </View>
          );
        })}
      </View>
    </View>
  );
}

// ─── Component: Medical Disclaimer (nhấp nháy) ───────────────────────
function MedicalDisclaimer() {
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 0.35,
          duration: 900,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 900,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, [pulseAnim]);

  return (
    <View style={styles.disclaimerCard}>
      {/* Icon cảnh báo nhấp nháy */}
      <Animated.View style={[styles.disclaimerIconWrap, { opacity: pulseAnim }]}>
        <Feather name="alert-triangle" size={18} color="#B45309" />
      </Animated.View>

      {/* Nội dung */}
      <View style={styles.disclaimerBody}>
        <Text style={styles.disclaimerTitle}>Lưu ý quan trọng</Text>
        <Text style={styles.disclaimerText}>
          Phân tích AI chỉ mang tính tham khảo, không thay thế chẩn đoán lâm sàng.
          {' '}<Text style={styles.disclaimerBold}>Luôn tham khảo bác sĩ</Text>{' '}
          để được điều trị an toàn và chính xác.
        </Text>
      </View>
    </View>
  );
}

// ─── Component: Wound Detail Tab Content ────────────────────────
function QuestionnaireAnswersSection({
  answers,
}: {
  answers: { questionText: string; selectedOptions: string[] }[];
}) {
  return (
    <View style={styles.answersCard}>
      <View style={styles.answersHeader}>
        <View style={styles.answersIconWrap}>
          <Feather name="clipboard" size={15} color={Colors.primary} />
        </View>
        <Text style={styles.answersTitle}>Câu trả lời của bạn</Text>
        <View style={styles.answersBadge}>
          <Text style={styles.answersBadgeText}>{answers.length} câu</Text>
        </View>
      </View>
      {answers.map((ans, idx) => (
        <View
          key={idx}
          style={[styles.answerRow, idx < answers.length - 1 && styles.answerRowBorder]}
        >
          <Text style={styles.answerQuestion}>
            {idx + 1}. {ans.questionText}
          </Text>
          <View style={styles.answerOptions}>
            {ans.selectedOptions.map((opt, oi) => (
              <View key={oi} style={styles.answerChip}>
                <Feather name="check" size={10} color={Colors.primary} />
                <Text style={styles.answerChipText}>{opt}</Text>
              </View>
            ))}
          </View>
        </View>
      ))}
    </View>
  );
}

function WoundDetailContent({ wound }: { wound: WoundDetail }) {
  return (
    <View style={styles.woundDetailContent}>
      <WoundScanCard wound={wound} />
      <MedicalDisclaimer />
      <View style={styles.recoveryCard}>
        <View style={styles.recoveryIconWrap}>
          <Feather name="clock" size={18} color={Colors.white} />
        </View>
        <View style={styles.recoveryInfo}>
          <Text style={styles.recoveryCardLabel}>Thời gian hồi phục dự kiến</Text>
          <Text style={styles.recoveryCardValue}>{wound.recoveryTime}</Text>
        </View>
        <View style={styles.recoveryPulse} />
      </View>
      <Text style={styles.firstAidHeading}>Quy trình sơ cứu</Text>
      {wound.firstAid.map((section, idx) => (
        <FirstAidSectionCard key={idx} section={section} />
      ))}
      {wound.userAnswers && wound.userAnswers.length > 0 && (
        <QuestionnaireAnswersSection answers={wound.userAnswers} />
      )}
    </View>
  );
}

// ─── Component: Chat Bubble ──────────────────────────────────────
function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  return (
    <View style={[styles.chatRow, isUser ? styles.chatRowUser : styles.chatRowBot]}>
      {!isUser && (
        <Image
          source={require('../assets/logo_DermAid.png')}
          style={styles.chatAvatar}
        />
      )}
      <View
        style={[
          styles.chatBubble,
          isUser ? styles.chatBubbleUser : styles.chatBubbleBot,
        ]}
      >
        <Text
          style={[
            styles.chatBubbleText,
            isUser ? styles.chatBubbleTextUser : styles.chatBubbleTextBot,
          ]}
        >
          {message.content}
        </Text>
        <Text
          style={[
            styles.chatTimestamp,
            isUser && styles.chatTimestampUser,
          ]}
        >
          {message.timestamp}
        </Text>
      </View>
    </View>
  );
}

// ─── Main Screen ─────────────────────────────────────────────────
export default function HistoryDetailScreen() {
  const insets = useSafeAreaInsets();
  const { analysisId } = useLocalSearchParams<{ analysisId: string }>();
  const chatScrollRef = useRef<ScrollView>(null);
  const { token } = useAuth();

  const [activeTab, setActiveTab] = useState<'detail' | 'chat'>('detail');
  const [activeWoundIndex, setActiveWoundIndex] = useState(0);

  const cachedData = analysisId ? globalDetailCache[analysisId] : undefined;
  const [detail, setDetail] = useState<AnalysisHistoryDetail | undefined>(cachedData);
  const [isLoading, setIsLoading] = useState(!cachedData);

  const fetchDetail = async (silent = false) => {
    try {
      if (!silent) setIsLoading(true);
      if (!analysisId) return;

      const [apiDetail, sessionsRes] = await Promise.all([
        getAnalysisDetail(analysisId),
        chatbotService.getSessions().catch(() => ({ data: { data: [] } }))
      ]);

      const d = new Date(apiDetail.analyzed_at);
      const dateStr = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`;

      // Resolve Questionnaire Text if user_responses exists
      let resolvedQnaires: any[] = [];
      if (apiDetail.user_responses && apiDetail.user_responses.length > 0 && apiDetail.significant_wounds?.length > 0) {
          try {
              const detectionsPayload = apiDetail.significant_wounds.map(w => ({
                  detection_id: w.detection_id || `temp_${Math.random()}`,
                  wound_type: w.wound_type,
                  subtype: w.sub_type,
                  severity: w.severity,
                  confidence: w.confidence_score
              }));
              resolvedQnaires = await resolveQuestionnaires(detectionsPayload);
          } catch(e) {
              console.log("Failed to resolve Qnaires", e);
          }
      }

      // Mapping wounds
      const wounds: WoundDetail[] = [];
      if (apiDetail.significant_wounds) {
        apiDetail.significant_wounds.forEach(w => {
          const rawLabel = mapWoundLabel(w.wound_type);
          const isChronic = ["psoriasis", "fungal", "acne"].includes(w.wound_type);
          const fd = w.firstaid_snapshot;

          const firstAid: FirstAidSection[] = [];
          // Ẩn "Sơ cứu ngay" với bệnh mãn tính (psoriasis / fungal)
          const isChronicType = ['psoriasis', 'fungal'].includes(w.wound_type);
          if (!isChronicType && fd && fd.steps?.length > 0) {
            firstAid.push({ title: 'Sơ cứu ngay', icon: '!' as any, steps: fd.steps.map(s => ({ content: s })) });
          }
          if (fd && fd.dos?.length > 0) {
            firstAid.push({ title: 'Nên làm', icon: 'check' as any, steps: fd.dos.map(s => ({ content: s })) });
          }
          if (fd && fd.donts?.length > 0) {
            firstAid.push({ title: 'Không nên làm', icon: 'x' as any, steps: fd.donts.map(s => ({ content: s })) });
          }

          let userAnswers: { questionText: string; selectedOptions: string[] }[] = [];
          if (apiDetail.user_responses && apiDetail.user_responses.length > 0 && resolvedQnaires.length > 0) {
             const matchingQnaire = resolvedQnaires.find(rq => rq.wound_type === w.wound_type);
             if (matchingQnaire) {
                const qMap = new Map();
                matchingQnaire.questionnaire.questions.forEach((q: any) => {
                   const matchedRes = apiDetail.user_responses!.filter((r: any) => r.question_id === q.question_id);
                   if (matchedRes.length > 0) {
                      const options = matchedRes.map((r: any) => {
                          const ans = q.answers.find((a: any) => a.answer_id === r.answer_id);
                          return ans ? ans.answer_text : null;
                      }).filter(Boolean) as string[];
                      
                      if (options.length > 0) {
                          qMap.set(q.question_id, {
                              questionText: q.question_text,
                              selectedOptions: options
                          });
                      }
                   }
                });
                userAnswers = Array.from(qMap.values());
             }
          }

          wounds.push({
            id: w.detection_id || `wound_${Math.random()}`,
            woundType: w.wound_type as any,
            imageUri: apiDetail.image_url.startsWith('http') ? apiDetail.image_url : `http://52.20.177.68${apiDetail.image_url}`,
            label: rawLabel,
            accuracy: Math.round((w.confidence_score || 0.85) * 100),
            boundingBox: { ...w.bounding_box },
            hasSeverity: !isChronic,
            severity: !isChronic ? (mapSeverityLabel(w.severity) as WoundDetail["severity"]) : undefined,
            severityColor: !isChronic ? mapSeverityColor(w.severity) : undefined,
            recoveryTime: fd?.estimated_healing_time || "Cần điều trị theo chỉ dẫn",
            firstAid,
            userAnswers
          });
        });
      }

      // Format Chat
      const sessionsList = (sessionsRes as any)?.data?.data || [];
      const session = sessionsList.find((s: any) => s.analysis_id === analysisId);
      
      let chatHistory: ChatMessage[] = [];
      if (session && session.session_id) {
        const chatDetailRes = await chatbotService.getSession(session.session_id).catch(() => null);
        if (chatDetailRes?.data?.data?.messages) {
           chatHistory = chatDetailRes.data.data.messages.map((m: any, i: number) => {
               const cmd = new Date(m.created_at);
               return {
                  id: `chat_${i}`,
                  role: m.role,
                  content: m.content,
                  timestamp: `${String(cmd.getHours()).padStart(2, '0')}:${String(cmd.getMinutes()).padStart(2, '0')}`
               };
           });
        }
      }

      const responseDetail = {
        id: apiDetail.analysis_id,
        date: dateStr,
        wounds,
        chatHistory
      };
      
      globalDetailCache[analysisId] = responseDetail;
      setDetail(responseDetail);
      
    } catch (e) {
      console.log("Failed to load history detail", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail(!!(analysisId && globalDetailCache[analysisId]));
  }, [analysisId, token]);

  // Scroll chat xuống cuối khi switch sang tab chat
  useEffect(() => {
    if (activeTab === 'chat') {
      setTimeout(() => {
        chatScrollRef.current?.scrollToEnd({ animated: false });
      }, 100);
    }
  }, [activeTab]);

  if (isLoading) {
    return (
      <View style={[styles.screen, { paddingTop: insets.top, justifyContent: 'center', alignItems: 'center' }]}>
        <StatusBar barStyle="dark-content" backgroundColor={Colors.backgroundSecondary} />
        <Text style={{ color: Colors.textMuted }}>Đang tải dữ liệu...</Text>
      </View>
    );
  }

  if (!detail || detail.wounds.length === 0) {
    return (
      <View style={[styles.screen, { paddingTop: insets.top }]}>
        <StatusBar barStyle="dark-content" backgroundColor={Colors.backgroundSecondary} />
        <View style={styles.topBar}>
          <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
            <Feather name="arrow-left" size={22} color={Colors.textPrimary} />
          </TouchableOpacity>
          <View style={styles.topBarCenter}>
            <Text style={styles.topBarTitle}>Chi tiết phân tích</Text>
          </View>
          <View style={styles.topBarSpacer} />
        </View>
        <View style={styles.notFoundState}>
          <Feather name="alert-circle" size={48} color={Colors.textMuted} />
          <Text style={styles.notFoundText}>Không tìm thấy dữ liệu phân tích</Text>
        </View>
      </View>
    );
  }

  const currentWound = detail.wounds[activeWoundIndex];
  const hasMultipleWounds = detail.wounds.length >= 2;

  return (
    <View style={[styles.screen, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" backgroundColor={Colors.backgroundSecondary} />

      {/* ── Top bar ── */}
      <View style={styles.topBar}>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Feather name="arrow-left" size={22} color={Colors.textPrimary} />
        </TouchableOpacity>
        <View style={styles.topBarCenter}>
          <Text style={styles.topBarTitle}>Chi tiết phân tích</Text>
          <Text style={styles.topBarDate}>{detail.date}</Text>
        </View>
        <TouchableOpacity style={styles.shareBtn}>
          <Feather name="share-2" size={20} color={Colors.textLight} />
        </TouchableOpacity>
      </View>

      {/* ── Main tab switcher ── */}
      <View style={styles.mainTabRow}>
        <TouchableOpacity
          style={[styles.mainTab, activeTab === 'detail' && styles.mainTabActive]}
          onPress={() => setActiveTab('detail')}
          activeOpacity={0.8}
        >
          <Text
            style={[
              styles.mainTabText,
              activeTab === 'detail' && styles.mainTabTextActive,
            ]}
          >
            Chi tiết phân tích
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.mainTab, activeTab === 'chat' && styles.mainTabActive]}
          onPress={() => setActiveTab('chat')}
          activeOpacity={0.8}
        >
          <Text
            style={[
              styles.mainTabText,
              activeTab === 'chat' && styles.mainTabTextActive,
            ]}
          >
            Tư vấn cùng DermAid
          </Text>
        </TouchableOpacity>
      </View>

      {/* ── TAB 1: Chi tiết phân tích ── */}
      {activeTab === 'detail' && (
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={[
            styles.scrollContent,
            { paddingBottom: insets.bottom + 24 },
          ]}
        >
          {/* Sub-tabs vết thương (chỉ hiện khi có >= 2 vết) */}
          {hasMultipleWounds && (
            <View style={styles.woundTabRow}>
              {detail.wounds.map((_, idx) => (
                <TouchableOpacity
                  key={idx}
                  style={[
                    styles.woundTab,
                    activeWoundIndex === idx && styles.woundTabActive,
                  ]}
                  onPress={() => setActiveWoundIndex(idx)}
                  activeOpacity={0.8}
                >
                  <Text
                    style={[
                      styles.woundTabText,
                      activeWoundIndex === idx && styles.woundTabTextActive,
                    ]}
                  >
                    Vết {idx + 1}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          )}

          {/* Nội dung chi tiết vết thương hiện tại */}
          <WoundDetailContent wound={currentWound} />
        </ScrollView>
      )}

      {/* ── TAB 2: Tư vấn DermAid (read-only) ── */}
      {activeTab === 'chat' && (
        <>
          {detail.chatHistory.length === 0 ? (
            /* Empty state */
            <View style={styles.chatEmptyState}>
              <View style={styles.chatEmptyIconWrap}>
                <Feather name="message-circle" size={40} color={Colors.textMuted} />
              </View>
              <Text style={styles.chatEmptyTitle}>Không có đoạn hội thoại nào</Text>
              <Text style={styles.chatEmptySubtext}>
                Bạn chưa tư vấn với DermAid về lần phân tích này
              </Text>
            </View>
          ) : (
            /* Danh sách chat read-only */
            <ScrollView
              ref={chatScrollRef}
              showsVerticalScrollIndicator={false}
              contentContainerStyle={[
                styles.chatScrollContent,
                { paddingBottom: insets.bottom + 24 },
              ]}
              onContentSizeChange={() => {
                chatScrollRef.current?.scrollToEnd({ animated: false });
              }}
            >
              {/* Date separator */}
              <View style={styles.chatDateSeparator}>
                <View style={styles.chatDateLine} />
                <Text style={styles.chatDateLabel}>{detail.date}</Text>
                <View style={styles.chatDateLine} />
              </View>

              {detail.chatHistory.map((msg) => (
                <ChatBubble key={msg.id} message={msg} />
              ))}

              {/* Read-only notice */}
              <View style={styles.readOnlyNotice}>
                <Feather name="lock" size={12} color={Colors.textMuted} />
                <Text style={styles.readOnlyText}>Chế độ xem lại — không thể gửi tin nhắn</Text>
              </View>
            </ScrollView>
          )}
        </>
      )}
    </View>
  );
}

// ─── Styles ──────────────────────────────────────────────────────
const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: Colors.backgroundSecondary,
  },

  // ── Top bar ──
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: Colors.backgroundSecondary,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  topBarCenter: {
    flex: 1,
    alignItems: 'center',
  },
  topBarTitle: {
    fontSize: 16,
    fontFamily: 'Inter_700Bold',
    color: Colors.textPrimary,

  },
  topBarDate: {
    fontSize: 12,
    fontFamily: 'Inter_400Regular',
    color: Colors.textMuted,
    marginTop: 2,
  },
  shareBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  topBarSpacer: { width: 40 },

  // ── Main tabs ──
  mainTabRow: {
    flexDirection: 'row',
    marginHorizontal: 16,
    marginBottom: 12,
    backgroundColor: Colors.backgroundTertiary,
    borderRadius: 12,
    padding: 4,
  },
  mainTab: {
    flex: 1,
    paddingVertical: 9,
    alignItems: 'center',
    borderRadius: 10,
  },
  mainTabActive: {
    backgroundColor: Colors.background,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  mainTabText: {
    fontSize: 13,
    fontFamily: 'Inter_600SemiBold',
    color: Colors.textMuted,
  },
  mainTabTextActive: {
    color: Colors.primary,
  },

  // ── Scroll content ──
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 4,
  },

  // ── Wound sub-tabs ──
  woundTabRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
    flexWrap: 'wrap',
  },
  woundTab: {
    paddingHorizontal: 18,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: Colors.backgroundTertiary,
    borderWidth: 1.5,
    borderColor: Colors.borderLight,
  },
  woundTabActive: {
    backgroundColor: Colors.primary + '15',
    borderColor: Colors.primary,
  },
  woundTabText: {
    fontSize: 13,
    fontFamily: 'Inter_600SemiBold',
    color: Colors.textLight,
  },
  woundTabTextActive: {
    color: Colors.primary,
  },

  // ── Wound detail content ──
  woundDetailContent: {
    gap: 14,
  },

  // ── Medical Disclaimer ──
  disclaimerCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: '#FFFBEB',
    borderWidth: 1,
    borderColor: '#FDE68A',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  disclaimerIconWrap: {
    marginTop: 1,
    flexShrink: 0,
  },
  disclaimerBody: {
    flex: 1,
    gap: 3,
  },
  disclaimerTitle: {
    fontSize: 12,
    fontFamily: 'Inter_700Bold',
    color: '#92400E',
    letterSpacing: 0.2,
  },
  disclaimerText: {
    fontSize: 12,
    fontFamily: 'Inter_400Regular',
    color: '#78350F',
    lineHeight: 18,
  },
  disclaimerBold: {
    fontFamily: 'Inter_700Bold',
    color: '#92400E',
  },

  // ── Medical Scan Card ──
  scanCard: {
    backgroundColor: Colors.background,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 5,
  },
  scanImageZone: {
    width: '100%',
    height: 230,
    backgroundColor: '#0F1923',
    position: 'relative',
  },
  scanImagePlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0F1923',
    gap: 8,
  },
  scanGrid: {
    ...StyleSheet.absoluteFillObject,
  },
  scanGridLineH: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 1,
    backgroundColor: 'rgba(2,161,141,0.1)',
  },
  scanGridLineV: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    width: 1,
    backgroundColor: 'rgba(2,161,141,0.1)',
  },
  scanPlaceholderText: {
    fontSize: 12,
    fontFamily: 'Inter_400Regular',
    color: 'rgba(2,161,141,0.5)',
    letterSpacing: 1.5,
    textTransform: 'uppercase',
  },
  // Bounding box corners
  boxCorner: {
    position: 'absolute',
    width: 10,
    height: 10,
    borderColor: Colors.primary,
  },
  boxCornerTL: { top: -1, left: -1, borderTopWidth: 3, borderLeftWidth: 3, borderTopLeftRadius: 4 },
  boxCornerTR: { top: -1, right: -1, borderTopWidth: 3, borderRightWidth: 3, borderTopRightRadius: 4 },
  boxCornerBL: { bottom: -1, left: -1, borderBottomWidth: 3, borderLeftWidth: 3, borderBottomLeftRadius: 4 },
  boxCornerBR: { bottom: -1, right: -1, borderBottomWidth: 3, borderRightWidth: 3, borderBottomRightRadius: 4 },
  // AI chip
  aiChip: {
    position: 'absolute',
    top: 12,
    right: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: 'rgba(2,161,141,0.18)',
    borderWidth: 1,
    borderColor: 'rgba(2,161,141,0.4)',
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  aiChipDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.primary,
  },
  aiChipText: {
    fontSize: 10,
    fontFamily: 'Inter_600SemiBold',
    color: Colors.primary,
    letterSpacing: 0.5,
  },
  // Gradient overlay với tên loại
  scanGradient: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 16,
    paddingTop: 28,
    paddingBottom: 14,
  },
  scanWoundType: {
    fontSize: 9,
    fontFamily: 'Inter_600SemiBold',
    color: 'rgba(255,255,255,0.6)',
    letterSpacing: 2,
    marginBottom: 3,
  },
  scanWoundLabel: {
    fontSize: 22,
    fontFamily: 'Inter_700Bold',
    color: Colors.white,
    letterSpacing: 0.3,
  },
  // Info panel
  scanInfoPanel: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
    gap: 16,
  },
  scanInfoLeft: {
    flex: 1,
  },
  scanInfoCaption: {
    fontSize: 9,
    fontFamily: 'Inter_700Bold',
    color: Colors.textMuted,
    letterSpacing: 1.5,
    marginBottom: 6,
  },
  scanAccuracyRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 4,
    marginBottom: 6,
  },
  scanAccuracyValue: {
    fontSize: 28,
    fontFamily: 'Inter_700Bold',
    color: Colors.primary,
    lineHeight: 32,
  },
  scanAccuracyTrack: {
    height: 5,
    backgroundColor: Colors.borderLight,
    borderRadius: 3,
    overflow: 'hidden',
  },
  scanAccuracyFill: {
    height: '100%',
    backgroundColor: Colors.primary,
    borderRadius: 3,
  },
  scanInfoDivider: {
    width: 1,
    height: 56,
    backgroundColor: Colors.borderLight,
  },
  scanInfoRight: {
    width: 110,
    alignItems: 'flex-start',
  },
  scanSeverityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderWidth: 1.5,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 5,
    marginBottom: 5,
    alignSelf: 'flex-start',
  },
  scanSeverityDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
  },
  scanSeverityText: {
    fontSize: 14,
    fontFamily: 'Inter_700Bold',
  },
  scanSeverityNote: {
    fontSize: 10,
    fontFamily: 'Inter_400Regular',
    color: Colors.textMuted,
  },
  scanNoSeverityText: {
    fontSize: 13,
    fontFamily: 'Inter_700Bold',
    color: Colors.textLight,
    lineHeight: 18,
    marginBottom: 4,
  },

  // ── Recovery card (giữ nguyên) ──
  recoveryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.primary,
    borderRadius: 12,
    padding: 16,
    gap: 14,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  recoveryIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  recoveryInfo: {
    flex: 1,
  },
  recoveryCardLabel: {
    fontSize: 12,
    fontFamily: 'Inter_400Regular',
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 2,
  },
  recoveryCardValue: {
    fontSize: 18,
    fontFamily: 'Inter_700Bold',
    color: Colors.white,
  },
  recoveryPulse: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(255,255,255,0.4)',
    alignSelf: 'center',
  },

  // ── First Aid heading ──
  firstAidHeading: {
    fontSize: 15,
    fontFamily: 'Inter_700Bold',
    color: Colors.textPrimary,
    marginTop: 4,
    marginBottom: 2,
    letterSpacing: 0.3,
  },

  // ── First Aid Group (card bao ngoài) ──
  firstAidGroup: {
    backgroundColor: Colors.background,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 10,
    elevation: 3,
    marginBottom: 2,
  },

  // ── Header của từng section ──
  firstAidHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 12,
    gap: 12,
  },
  firstAidIconBadge: {
    width: 34,
    height: 34,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  firstAidIconChar: {
    fontSize: 16,
    fontFamily: 'Inter_700Bold',
    color: Colors.white,
  },
  firstAidHeaderText: {
    flex: 1,
  },
  firstAidTitle: {
    fontSize: 14,
    fontFamily: 'Inter_700Bold',
    lineHeight: 18,
  },
  firstAidTag: {
    fontSize: 9,
    fontFamily: 'Inter_600SemiBold',
    letterSpacing: 1.2,
    marginTop: 1,
    opacity: 0.75,
  },
  firstAidStepCount: {
    flexDirection: 'row',
    alignItems: 'baseline',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
  firstAidStepCountText: {
    fontSize: 14,
    fontFamily: 'Inter_700Bold',
    color: Colors.white,
  },
  firstAidStepCountLabel: {
    fontSize: 9,
    fontFamily: 'Inter_700Bold',
    color: 'rgba(255,255,255,0.85)',
    letterSpacing: 0.5,
  },

  // ── Timeline ──
  timelineContainer: {
    paddingHorizontal: 14,
    paddingTop: 10,
    paddingBottom: 16,
    backgroundColor: Colors.background,
  },
  timelineRow: {
    flexDirection: 'row',
    gap: 12,
  },
  timelineLeft: {
    alignItems: 'center',
    width: 30,
  },
  timelineCircle: {
    width: 30,
    height: 30,
    borderRadius: 15,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  timelineNumber: {
    fontSize: 13,
    fontFamily: 'Inter_700Bold',
  },
  timelineLine: {
    width: 2,
    flex: 1,
    minHeight: 12,
    marginVertical: 3,
    borderRadius: 1,
    opacity: 0.4,
  },
  timelineContent: {
    flex: 1,
    paddingTop: 5,
    paddingBottom: 16,
  },
  timelineContentLast: {
    paddingBottom: 0,
  },
  timelineText: {
    fontSize: 13.5,
    fontFamily: 'Inter_400Regular',
    color: Colors.textPrimary,
    lineHeight: 21,
  },

  // (giữ lại để tránh lỗi nếu code cũ còn ref)
  firstAidIconCircle: { width: 0, height: 0 },
  firstAidIconText: { fontSize: 0 },
  stepCard: { flexDirection: 'row' },
  stepNumber: { width: 0, height: 0 },
  stepNumberText: { fontSize: 0 },
  stepContent: { flex: 1, fontSize: 0 },

  // ── Not found state ──
  notFoundState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  notFoundText: {
    fontSize: 15,
    fontFamily: 'Inter_600SemiBold',
    color: Colors.textMuted,
    textAlign: 'center',
  },

  // ── Chat tab ──
  chatScrollContent: {
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  chatDateSeparator: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 10,
  },
  chatDateLine: {
    flex: 1,
    height: 1,
    backgroundColor: Colors.borderChatDate,
  },
  chatDateLabel: {
    fontSize: 12,
    fontFamily: 'Inter_600SemiBold',
    color: Colors.chatDateText,
    backgroundColor: Colors.chatDateBg,
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 20,
  },
  chatRow: {
    flexDirection: 'row',
    marginBottom: 12,
    maxWidth: '82%',
    alignItems: 'flex-end',
  },
  chatRowBot: {
    alignSelf: 'flex-start',
  },
  chatRowUser: {
    alignSelf: 'flex-end',
    flexDirection: 'row-reverse',
  },
  chatAvatar: {
    width: 30,
    height: 30,
    borderRadius: 15,
    marginRight: 8,
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.borderChatDate,
  },
  chatBubble: {
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 10,
    maxWidth: '100%',
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.07,
    shadowRadius: 4,
    elevation: 2,
  },
  chatBubbleBot: {
    backgroundColor: Colors.backgroundTertiary,
    borderBottomLeftRadius: 4,
  },
  chatBubbleUser: {
    backgroundColor: Colors.chatUserBg,
    borderBottomRightRadius: 4,
  },
  chatBubbleText: {
    fontSize: 14,
    fontFamily: 'Inter_400Regular',
    lineHeight: 20,
  },
  chatBubbleTextBot: {
    color: Colors.textPrimary,
  },
  chatBubbleTextUser: {
    color: Colors.white,
  },
  chatTimestamp: {
    fontSize: 10,
    fontFamily: 'Inter_400Regular',
    color: Colors.textMuted,
    marginTop: 4,
    textAlign: 'right',
  },
  chatTimestampUser: {
    color: 'rgba(255,255,255,0.65)',
  },

  // Read-only notice
  readOnlyNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 16,
    paddingVertical: 10,
    backgroundColor: Colors.backgroundTertiary,
    borderRadius: 20,
  },
  readOnlyText: {
    fontSize: 12,
    fontFamily: 'Inter_400Regular',
    color: Colors.textMuted,
  },

  // Empty state chat
  chatEmptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    paddingHorizontal: 32,
  },
  chatEmptyIconWrap: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.backgroundTertiary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  chatEmptyTitle: {
    fontSize: 16,
    fontFamily: 'Inter_700Bold',
    color: Colors.textPrimary,
    textAlign: 'center',
  },
  chatEmptySubtext: {
    fontSize: 13,
    fontFamily: 'Inter_400Regular',
    color: Colors.textMuted,
    textAlign: 'center',
    lineHeight: 19,
  },

  // ── Questionnaire Answers Section ──
  answersCard: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    marginTop: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: `${Colors.primary}22`,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  answersHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: `${Colors.primary}0A`,
    borderBottomWidth: 1,
    borderBottomColor: `${Colors.primary}18`,
  },
  answersIconWrap: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: `${Colors.primary}18`,
    alignItems: 'center',
    justifyContent: 'center',
  },
  answersTitle: {
    flex: 1,
    fontSize: 14,
    fontWeight: '700',
    color: Colors.textPrimary,
    fontFamily: 'Inter_700Bold',
  },
  answersBadge: {
    backgroundColor: Colors.primary,
    borderRadius: 20,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  answersBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.white,
  },
  answerRow: {
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  answerRowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: Colors.backgroundTertiary,
  },
  answerQuestion: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textPrimary,
    fontFamily: 'Inter_600SemiBold',
    marginBottom: 6,
  },
  answerOptions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  answerChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: `${Colors.primary}12`,
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: `${Colors.primary}25`,
  },
  answerChipText: {
    fontSize: 12,
    color: Colors.primary,
    fontWeight: '600',
    fontFamily: 'Inter_600SemiBold',
  },
});
