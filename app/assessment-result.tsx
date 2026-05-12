// app/assessment-result.tsx
// TODO-5: Hiển thị kết quả từ LLM synthesis hoặc firstaid_snapshot (fallback)
// - synthesisJson rỗng ('') → dùng firstaid_snapshot từ selectedDetections
// - Lưu ý quan trọng (Medical Disclaimer) đặt LÊN ĐẦU

import { Feather } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router, useLocalSearchParams } from 'expo-router';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Animated,
  Image,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Colors } from '../constants/colors';
import { FirstAidSection, WoundDetail } from '../constants/analysisTypes';
import {
  SignificantWound,
  SynthesisResult,
  mapWoundLabel,
  mapWoundTypeId,
  mapSeverityColor,
  mapSeverityLabel,
} from '../services/woundService';

// ─── Màu section first aid ──────────────────────────────────────────────────
const SECTION_COLORS = {
  'Sơ cứu ngay': {
    headerBg: '#DCFCE7',
    iconColor: '#16A34A',
    stepNumberBg: '#DCFCE7',
    stepNumberBorder: '#86EFAC',
    stepNumberColor: '#16A34A',
    icon: '!',
    tag: 'KHẨN CẤP',
  },
  'Nên làm': {
    headerBg: '#DBEAFE',
    iconColor: '#2563EB',
    stepNumberBg: '#DBEAFE',
    stepNumberBorder: '#93C5FD',
    stepNumberColor: '#2563EB',
    icon: '✓',
    tag: 'KHUYẾN NGHỊ',
  },
  'Không nên làm': {
    headerBg: '#FED7AA',
    iconColor: '#F97316',
    stepNumberBg: '#FFF7ED',
    stepNumberBorder: '#FDBA74',
    stepNumberColor: '#F97316',
    icon: '✕',
    tag: 'CẢNH BÁO',
  },
} as const;

// ─── Helpers: Build WoundDetail từ API data ─────────────────────────────────

// Guide có thể là FirstAidSnapshot (từ API-2) hoặc structured_guidance từ LLM synthesis
// Cả hai đều có steps/dos/donts/estimated_healing_time nhưng source là optional ở LLM
type GuideInput = {
  title?: string;
  steps?: string[];
  dos?: string[];
  donts?: string[];
  supplies_needed?: string[];
  estimated_healing_time?: string;
  source?: string | null;
} | null;

// suppressImmediate = true → ẩn section "Sơ cứu ngay" (dùng cho bệnh mãn tính psoriasis/fungal)
function buildFirstAidSections(guide: GuideInput, suppressImmediate = false): FirstAidSection[] {
  if (!guide) return [];
  const sections: FirstAidSection[] = [];

  if (!suppressImmediate && guide.steps && guide.steps.length > 0) {
    sections.push({
      title: 'Sơ cứu ngay',
      icon: 'alert',
      steps: guide.steps.map((content) => ({ content })) as { content: string }[],
    });
  }
  if (guide.dos && guide.dos.length > 0) {
    sections.push({
      title: 'Nên làm',
      icon: 'check',
      steps: guide.dos.map((content) => ({ content })) as { content: string }[],
    });
  }
  if (guide.donts && guide.donts.length > 0) {
    sections.push({
      title: 'Không nên làm',
      icon: 'ban',
      steps: guide.donts.map((content) => ({ content })) as { content: string }[],
    });
  }
  return sections;
}

function findSynthesis(
  wound: SignificantWound,
  syntheses: SynthesisResult[] | null
): SynthesisResult | null {
  if (!syntheses) return null;
  return (
    syntheses.find(
      (s) => s.wound_type === wound.wound_type && s.subtype === wound.sub_type
    ) ?? null
  );
}

// Các wound_type mãn tính không cần mục "Sơ cứu ngay"
const CHRONIC_TYPES = ['psoriasis', 'fungal'] as const;

function buildWoundDetail(
  wound: SignificantWound,
  synthesis: SynthesisResult | null,
  imageUri: string
): WoundDetail {
  const guide: GuideInput = synthesis?.structured_guidance ?? wound.firstaid_snapshot;
  const isFallback = !synthesis?.structured_guidance;
  const hasSeverity = !['psoriasis', 'fungal', 'acne'].includes(wound.wound_type);
  const severityColor = mapSeverityColor(wound.severity);
  // Ẩn "Sơ cứu ngay" với các bệnh mãn tính (psoriasis / fungal)
  const suppressImmediate = (CHRONIC_TYPES as readonly string[]).includes(wound.wound_type);

  return {
    id: wound.detection_id,
    woundType: mapWoundTypeId(wound.wound_type),
    label: mapWoundLabel(wound.wound_type),
    accuracy: Math.round(wound.confidence_score * 100),
    hasSeverity,
    severity: hasSeverity ? (mapSeverityLabel(wound.severity) as any) : undefined,
    severityColor: hasSeverity ? severityColor : undefined,
    recoveryTime: guide?.estimated_healing_time ?? '—',
    // boundingBox lưu giá trị pixel gốc từ API (không hóa 0-1)
    // WoundScanCard sẽ tự normalize bằng Image.getSize()
    boundingBox: wound.bounding_box,
    imageUri,
    firstAid: buildFirstAidSections(guide, suppressImmediate),
    isFallback,
  };
}

// ─── Placeholder WOUND_DETAILS_MAP (giữ lại cho backward compat) ─────────────
// Không còn được dùng để build wounds từ API — chỉ giữ để tránh break imports
const WOUND_DETAILS_MAP_PLACEHOLDER: Record<string, WoundDetail> = {
  bong: {
    id: 'bong',
    woundType: 'bỏng',
    label: 'Bỏng',
    accuracy: 94,
    hasSeverity: true,
    severity: 'Nặng',
    severityColor: '#DC2626',
    recoveryTime: '10–21 ngày (tùy mức độ)',
    boundingBox: { x: 0.25, y: 0.2, width: 0.5, height: 0.45 },
    imageUri: 'placeholder',
    firstAid: [
      {
        title: 'Sơ cứu ngay',
        icon: 'alert',
        steps: [
          { content: 'Rửa vết bỏng dưới vòi nước mát sạch ít nhất 10–15 phút để hạ nhiệt.' },
          { content: 'Tháo nhẹ đồ trang sức, quần áo gần vùng bỏng trước khi nó sưng lên.' },
        ],
      },
      {
        title: 'Nên làm',
        icon: 'check',
        steps: [
          { content: 'Bôi gel làm dịu (Aloe Vera) và che phủ bằng băng gạc vô trùng.' },
          { content: 'Uống Paracetamol nếu đau nhiều. Đến bệnh viện nếu diện tích lớn hơn 1 bàn tay.' },
        ],
      },
      {
        title: 'Không nên làm',
        icon: 'ban',
        steps: [
          { content: 'Tuyệt đối không chọc vỡ bọng nước — nguy cơ nhiễm trùng cao.' },
          { content: 'Không dùng nước đá, kem đánh răng hoặc bơ đắp lên vết bỏng.' },
        ],
      },
    ],
  },
  tray: {
    id: 'tray',
    woundType: 'trầy',
    label: 'Trầy xước',
    accuracy: 91,
    hasSeverity: true,
    severity: 'Nhẹ',
    severityColor: '#059669',
    recoveryTime: '3–10 ngày',
    boundingBox: { x: 0.15, y: 0.2, width: 0.5, height: 0.4 },
    imageUri: 'placeholder',
    firstAid: [
      {
        title: 'Sơ cứu ngay',
        icon: 'alert',
        steps: [
          { content: 'Rửa sạch vết thương bằng nước sạch hoặc nước muối sinh lý 0.9%.' },
          { content: 'Dùng nhíp đã khử trùng loại bỏ dị vật nhỏ nếu có.' },
        ],
      },
      {
        title: 'Nên làm',
        icon: 'check',
        steps: [
          { content: 'Bôi dung dịch sát khuẩn (Povidone-iodine / chlorhexidine) lên vùng trầy.' },
          { content: 'Băng bằng gạc sạch, thay băng mỗi ngày một lần.' },
        ],
      },
      {
        title: 'Không nên làm',
        icon: 'ban',
        steps: [
          { content: 'Không gãi hoặc cạy lớp vảy đóng trên vết thương khi đang lành.' },
          { content: 'Không để vùng trầy tiếp xúc trực tiếp với bụi bẩn.' },
        ],
      },
    ],
  },
  bam: {
    id: 'bam',
    woundType: 'bầm',
    label: 'Vết bầm',
    accuracy: 89,
    hasSeverity: true,
    severity: 'Trung bình',
    severityColor: '#CA8A04',
    recoveryTime: '5–10 ngày',
    boundingBox: { x: 0.2, y: 0.25, width: 0.45, height: 0.38 },
    imageUri: 'placeholder',
    firstAid: [
      {
        title: 'Sơ cứu ngay',
        icon: 'alert',
        steps: [
          { content: 'Chườm lạnh ngay bằng túi đá bọc trong khăn vải khoảng 20 phút.' },
        ],
      },
      {
        title: 'Nên làm',
        icon: 'check',
        steps: [
          { content: 'Nâng cao vùng bị bầm (nếu ở tay/chân) để giảm tụ máu.' },
          { content: 'Sau 48 giờ có thể chườm ấm để tăng tuần hoàn, giúp nhanh tan bầm.' },
        ],
      },
      {
        title: 'Không nên làm',
        icon: 'ban',
        steps: [
          { content: 'Không xoa bóp mạnh lên vùng bầm trong 24 giờ đầu.' },
          { content: 'Không tự ý uống thuốc chống đông máu mà không có chỉ định.' },
        ],
      },
    ],
  },
  'mun-trung-ca': {
    id: 'mun-trung-ca',
    woundType: 'mụn trứng cá',
    label: 'Mụn trứng cá',
    accuracy: 88,
    hasSeverity: true,
    severity: 'Trung bình',
    severityColor: '#CA8A04',
    recoveryTime: '7–21 ngày',
    boundingBox: { x: 0.2, y: 0.15, width: 0.55, height: 0.5 },
    imageUri: 'placeholder',
    firstAid: [
      {
        title: 'Sơ cứu ngay',
        icon: 'alert',
        steps: [
          { content: 'Rửa mặt nhẹ nhàng với sữa rửa mặt dịu nhẹ 2 lần/ngày, không chà xát mạnh.' },
        ],
      },
      {
        title: 'Nên làm',
        icon: 'check',
        steps: [
          { content: 'Dùng kem trị mụn chứa benzoyl peroxide hoặc salicylic acid nồng độ thấp.' },
          { content: 'Giữ da sạch, tránh chạm tay bẩn lên mặt, thay vỏ gối thường xuyên.' },
        ],
      },
      {
        title: 'Không nên làm',
        icon: 'ban',
        steps: [
          { content: 'Không nặn mụn — dễ gây viêm nhiễm sâu hơn và để lại sẹo thâm.' },
          { content: 'Tránh dùng kem dưỡng có dầu khoáng (mineral oil) nếu da đang mọc mụn.' },
        ],
      },
    ],
  },
  'vay-nen': {
    id: 'vay-nen',
    woundType: 'vảy nến',
    label: 'Vảy nến',
    accuracy: 82,
    hasSeverity: false,
    recoveryTime: 'Cần điều trị lâu dài, tái khám định kỳ',
    boundingBox: { x: 0.15, y: 0.2, width: 0.55, height: 0.5 },
    imageUri: 'placeholder',
    firstAid: [
      {
        title: 'Nên làm',
        icon: 'check',
        steps: [
          { content: 'Dưỡng ẩm da thường xuyên bằng kem không mùi, không cồn để giảm bong vảy.' },
          { content: 'Tắm nước ấm (không nóng), tránh kỳ cọ mạnh lên vùng da bệnh.' },
          { content: 'Đến gặp bác sĩ da liễu để được kê liệu trình phù hợp với mức độ bệnh.' },
        ],
      },
      {
        title: 'Không nên làm',
        icon: 'ban',
        steps: [
          { content: 'Không tự ý dùng corticosteroid mạnh mà không có chỉ định của bác sĩ.' },
          { content: 'Tránh tiếp xúc với hóa chất tẩy rửa, xà phòng nồng độ cao.' },
        ],
      },
    ],
  },
  'nam-da': {
    id: 'nam-da',
    woundType: 'nấm da',
    label: 'Nấm da',
    accuracy: 85,
    hasSeverity: false,
    recoveryTime: '2–4 tuần điều trị kháng nấm',
    boundingBox: { x: 0.2, y: 0.2, width: 0.5, height: 0.45 },
    imageUri: 'placeholder',
    firstAid: [
      {
        title: 'Sơ cứu ngay',
        icon: 'alert',
        steps: [
          { content: 'Giữ vùng da bị nhiễm luôn sạch và khô ráo — nấm phát triển mạnh trong môi trường ẩm ướt.' },
        ],
      },
      {
        title: 'Nên làm',
        icon: 'check',
        steps: [
          { content: 'Bôi thuốc kháng nấm tại chỗ (clotrimazole / miconazole) đúng liều theo hướng dẫn.' },
          { content: 'Thay quần áo, khăn tắm mỗi ngày. Không dùng chung đồ cá nhân với người khác.' },
        ],
      },
      {
        title: 'Không nên làm',
        icon: 'ban',
        steps: [
          { content: 'Không tự ý ngừng thuốc dù triệu chứng thuyên giảm — nấm có thể tái phát.' },
          { content: 'Tránh mặc quần áo chật, bằng sợi tổng hợp giữ nhiệt ở vùng da bệnh.' },
        ],
      },
    ],
  },
};
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const _WOUND_DETAILS_MAP = WOUND_DETAILS_MAP_PLACEHOLDER;

// ─── Cấu hình màu gradient cho từng wound type ───────────────────────────────
const WOUND_ACCENT: Record<string, string> = {
  bong: '#E87440',
  tray: '#E05050',
  bam: '#4A7CB5',
  'mun-trung-ca': '#3A7BD5',
  'vay-nen': '#C04A3A',
  'nam-da': '#7B4FD5',
};

// ─── Sub-component: Medical Disclaimer (pulsing) ─────────────────────────────
function MedicalDisclaimer() {
  const cardFlash = useRef(new Animated.Value(1)).current;
  const iconPulse = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    // Cả card nhấp nháy như đèn cảnh báo
    Animated.loop(
      Animated.sequence([
        Animated.timing(cardFlash, { toValue: 0.48, duration: 420, useNativeDriver: true }),
        Animated.timing(cardFlash, { toValue: 1, duration: 420, useNativeDriver: true }),
      ])
    ).start();
    // Icon lệch pha
    Animated.loop(
      Animated.sequence([
        Animated.timing(iconPulse, { toValue: 0.2, duration: 800, useNativeDriver: true }),
        Animated.timing(iconPulse, { toValue: 1, duration: 800, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  return (
    <Animated.View style={[styles.disclaimerCard, { opacity: cardFlash }]}>
      <Animated.View style={[styles.disclaimerIcon, { opacity: iconPulse }]}>
        <Feather name="alert-triangle" size={20} color="#B45309" />
      </Animated.View>
      <View style={styles.disclaimerBody}>
        <Text style={styles.disclaimerTitle}>⚠️  Lưu ý quan trọng</Text>
        <Text style={styles.disclaimerText}>
          Phân tích AI chỉ mang tính tham khảo, không thay thế chẩn đoán lâm sàng.{' '}
          <Text style={styles.disclaimerBold}>Luôn tham khảo bác sĩ</Text>
          {' '}để được điều trị an toàn và chính xác.
        </Text>
      </View>
    </Animated.View>
  );
}

// ─── Sub-component: Medical Scan Card ────────────────────────────────────────
function WoundScanCard({ wound }: { wound: WoundDetail }) {
  // Kích thước render của zone ảnh (layout) — để scale bounding box
  const [renderSize, setRenderSize] = useState({ width: 0, height: 0 });
  // Kích thước ảnh gốc (pixel) — để normalize bounding box từ pixel → 0-1 → render px
  const [origSize, setOrigSize] = useState({ width: 0, height: 0 });
  const accentColor = WOUND_ACCENT[wound.woundType] ?? Colors.primary;
  const fillColor = wound.accuracy >= 65 ? Colors.primary : wound.accuracy >= 45 ? '#F59E0B' : '#EF4444';

  // Lấy kích thước pixel gốc của ảnh khi có URI
  useEffect(() => {
    if (wound.imageUri && wound.imageUri !== 'placeholder') {
      Image.getSize(
        wound.imageUri,
        (w, h) => setOrigSize({ width: w, height: h }),
        () => {}
      );
    }
  }, [wound.imageUri]);

  // Normalize bounding box: pixel → ratio (0-1) → render px
  const bb = (() => {
    const { x, y, width, height } = wound.boundingBox;
    if (
      renderSize.width > 0 &&
      renderSize.height > 0 &&
      origSize.width > 0 &&
      origSize.height > 0
    ) {
      // ảnh gốc có hệ số tỷ lệ khác render zone — tính theo cover mode
      const srcRatio = origSize.width / origSize.height;
      const dstRatio = renderSize.width / renderSize.height;
      let scaleX: number, scaleY: number, offsetX: number, offsetY: number;
      if (srcRatio > dstRatio) {
        // ảnh rộng hơn zone — cover theo chiều dọc
        scaleY = renderSize.height / origSize.height;
        scaleX = scaleY;
        offsetX = (renderSize.width - origSize.width * scaleX) / 2;
        offsetY = 0;
      } else {
        scaleX = renderSize.width / origSize.width;
        scaleY = scaleX;
        offsetX = 0;
        offsetY = (renderSize.height - origSize.height * scaleY) / 2;
      }
      return {
        left: x * scaleX + offsetX,
        top: y * scaleY + offsetY,
        width: width * scaleX,
        height: height * scaleY,
        visible: true,
      };
    }
    return { left: 0, top: 0, width: 0, height: 0, visible: false };
  })();

  const hasRealImage = !!wound.imageUri && wound.imageUri !== 'placeholder';

  return (
    <View style={styles.scanCard}>
      {/* Zone ảnh */}
      <View
        style={styles.scanImageZone}
        onLayout={(e) =>
          setRenderSize({
            width: e.nativeEvent.layout.width,
            height: e.nativeEvent.layout.height,
          })
        }
      >
        {/* Nền placeholder grid (hiện khi chưa load xong ảnh) */}
        <View style={styles.scanImagePlaceholder}>
          <View style={styles.scanGrid}>
            {[0.25, 0.5, 0.75].map((v) => (
              <View key={v} style={[styles.scanGridH, { top: `${v * 100}%` as any }]} />
            ))}
            {[0.33, 0.66].map((v) => (
              <View key={v} style={[styles.scanGridV, { left: `${v * 100}%` as any }]} />
            ))}
          </View>
          {!hasRealImage && (
            <>
              <Feather name="aperture" size={40} color="rgba(2,161,141,0.22)" />
              <Text style={styles.scanPlaceholderTxt}>ẢNH PHÂN TÍCH</Text>
            </>
          )}
        </View>

        {/* Ảnh thực từ imageUri — hiện đè lên placeholder */}
        {hasRealImage && (
          <Image
            source={{ uri: wound.imageUri }}
            style={StyleSheet.absoluteFillObject}
            resizeMode="cover"
          />
        )}

        {/* Bounding box overlay — chỉ vẽ khi đã tính được tọa độ */}
        {bb.visible && (
          <View
            style={{
              position: 'absolute',
              left: bb.left,
              top: bb.top,
              width: bb.width,
              height: bb.height,
              borderColor: accentColor,
              borderWidth: 2.5,
              borderRadius: 4,
            }}
          >
            <View style={[styles.corner, styles.cornerTL, { borderColor: accentColor }]} />
            <View style={[styles.corner, styles.cornerTR, { borderColor: accentColor }]} />
            <View style={[styles.corner, styles.cornerBL, { borderColor: accentColor }]} />
            <View style={[styles.corner, styles.cornerBR, { borderColor: accentColor }]} />
          </View>
        )}

        {/* AI chip */}
        <View style={styles.aiChip}>
          <View style={styles.aiChipDot} />
          <Text style={styles.aiChipTxt}>AI Detection</Text>
        </View>

        {/* Gradient overlay + label */}
        <LinearGradient
          colors={['transparent', 'rgba(0,0,0,0.75)']}
          style={styles.scanGradient}
        >
          <Text style={styles.scanTypeLabel}>LOẠI TỔN THƯƠNG</Text>
          <Text style={styles.scanWoundLabel}>{wound.label}</Text>
        </LinearGradient>
      </View>

      {/* Info panel */}
      <View style={styles.scanInfoPanel}>
        {/* Accuracy */}
        <View style={styles.scanInfoLeft}>
          <Text style={styles.scanInfoCaption}>ĐỘ TIN CẬY</Text>
          <Text style={styles.scanAccuracyVal}>{wound.accuracy}%</Text>
          <View style={styles.scanAccuracyTrack}>
            <View
              style={[
                styles.scanAccuracyFill,
                { width: `${wound.accuracy}%` as any, backgroundColor: fillColor },
              ]}
            />
          </View>
        </View>

        <View style={styles.scanInfoDivider} />

        {/* Severity */}
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
              <Text style={styles.scanNoSeverityText} numberOfLines={1}>Không phân loại</Text>
              <Text style={styles.scanSeverityNote}>Bệnh mãn tính</Text>
            </>
          )}
        </View>
      </View>
    </View>
  );
}

// ─── Sub-component: First Aid Section Card ───────────────────────────────────
function FirstAidSectionCard({ section }: { section: FirstAidSection }) {
  const cfg = SECTION_COLORS[section.title];
  return (
    <View style={styles.firstAidGroup}>
      {/* Header */}
      <View style={[styles.firstAidHeader, { backgroundColor: cfg.headerBg }]}>
        <View style={[styles.firstAidIconBadge, { backgroundColor: cfg.iconColor }]}>
          <Text style={styles.firstAidIconChar}>{cfg.icon}</Text>
        </View>
        <View style={styles.firstAidHeaderText}>
          <Text style={[styles.firstAidTitle, { color: cfg.iconColor }]}>
            {section.title}
          </Text>
          <Text style={[styles.firstAidTag, { color: cfg.iconColor }]}>{cfg.tag}</Text>
        </View>
        <View style={[styles.firstAidStepCount, { backgroundColor: cfg.iconColor }]}>
          <Text style={styles.firstAidStepCountNum}>{section.steps.length}</Text>
          <Text style={styles.firstAidStepCountLabel}> BƯỚC</Text>
        </View>
      </View>

      {/* Timeline steps */}
      <View style={styles.timelineWrap}>
        {section.steps.map((step, idx) => {
          const isLast = idx === section.steps.length - 1;
          return (
            <View key={idx} style={styles.timelineRow}>
              <View style={styles.timelineLeft}>
                <View
                  style={[
                    styles.timelineCircle,
                    { backgroundColor: cfg.stepNumberBg, borderColor: cfg.stepNumberBorder },
                  ]}
                >
                  <Text style={[styles.timelineNum, { color: cfg.stepNumberColor }]}>
                    {idx + 1}
                  </Text>
                </View>
                {!isLast && (
                  <View style={[styles.timelineLine, { backgroundColor: cfg.stepNumberBorder }]} />
                )}
              </View>
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

// ─── Sub-component: Recovery card ────────────────────────────────────────────
function RecoveryCard({ recoveryTime }: { recoveryTime: string }) {
  return (
    <View style={styles.recoveryCard}>
      <LinearGradient
        colors={[Colors.primary, Colors.primaryDark]}
        style={styles.recoveryIconCircle}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <Feather name="clock" size={18} color="#fff" />
      </LinearGradient>
      <View style={styles.recoveryInfo}>
        <Text style={styles.recoveryLabel}>Thời gian hồi phục dự kiến</Text>
        <Text style={styles.recoveryValue}>{recoveryTime}</Text>
      </View>
    </View>
  );
}

// ─── Main Screen ─────────────────────────────────────────────────────────────
export default function AssessmentResultScreen() {
  const insets = useSafeAreaInsets();
  const { analysisId, selectedDetections: rawDetections, synthesisJson, imageUri: rawUri } =
    useLocalSearchParams<{
      analysisId: string;
      selectedDetections: string;
      synthesisJson: string;   // rỗng ('') = LLM fallback, dùng firstaid_snapshot
      imageUri?: string;
    }>();

  // Parse selectedDetections (SignificantWound[])
  const selectedDetections: SignificantWound[] = useMemo(() => {
    try { return JSON.parse(rawDetections ?? '[]'); } catch { return []; }
  }, [rawDetections]);

  // Parse syntheses — null nếu synthesisJson rỗng (fallback mode)
  const syntheses: SynthesisResult[] | null = useMemo(() => {
    if (!synthesisJson) return null;
    try { return JSON.parse(synthesisJson); } catch { return null; }
  }, [synthesisJson]);

  // Build WoundDetail cho mỗi wound đã chọn
  const wounds: WoundDetail[] = useMemo(
    () =>
      selectedDetections.map((w) =>
        buildWoundDetail(w, findSynthesis(w, syntheses), rawUri ?? '')
      ),
    [selectedDetections, syntheses, rawUri]
  );

  const [activeIndex, setActiveIndex] = useState(0);
  const activeWound = wounds[activeIndex];

  // Entry animation
  const fadeIn = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.timing(fadeIn, { toValue: 1, duration: 500, useNativeDriver: true }).start();
  }, []);

  // Empty state
  if (wounds.length === 0) {
    return (
      <View style={[styles.root, { paddingTop: insets.top }]}>
        <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />
        <View style={styles.topBar}>
          <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
            <Feather name="arrow-left" size={20} color={Colors.primary} />
          </TouchableOpacity>
          <Text style={styles.topBarTitle}>KẾT QUẢ ĐÁNH GIÁ</Text>
          <View style={styles.topBarSpacer} />
        </View>
        <View style={styles.emptyState}>
          <Feather name="alert-circle" size={48} color={Colors.textMuted} />
          <Text style={styles.emptyText}>Không có dữ liệu vết thương</Text>
          <TouchableOpacity style={styles.emptyBtn} onPress={() => router.replace('/(tabs)/home')}>
            <Text style={styles.emptyBtnText}>Về trang chủ</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.root, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />

      {/* ── Top bar ─────────────────────────────────────────────── */}
      <View style={styles.topBar}>
        <TouchableOpacity
          style={styles.backBtn}
          onPress={() => router.back()}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Feather name="arrow-left" size={20} color={Colors.primary} />
        </TouchableOpacity>

        <View style={styles.topBarCenter}>
          <Text style={styles.topBarTitle}>KẾT QUẢ ĐÁNH GIÁ</Text>
          <Text style={styles.topBarSubtitle}>
            {wounds.length} vết thương được phân tích
          </Text>
        </View>

        {/* Share button — placeholder */}
        <TouchableOpacity style={styles.shareBtn}>
          <Feather name="share-2" size={18} color={Colors.textLight} />
        </TouchableOpacity>
      </View>

      {/* ── Scrollable content ────────────────────────────────── */}
      <Animated.ScrollView
        style={styles.scroll}
        contentContainerStyle={[
          styles.scrollContent,
          { paddingBottom: insets.bottom + 100 },
        ]}
        showsVerticalScrollIndicator={false}
      >
        {/* ① Lưu ý quan trọng — ĐẦU TIÊN */}
        <MedicalDisclaimer />

        {/* ② Wound selector tabs (nếu có nhiều hơn 1 vết) */}
        {wounds.length > 1 && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.woundTabRow}
          >
            {wounds.map((w, idx) => {
              // wound.woundType là FE ID (tray/bam/bong...), dùng để lookup accent
              const acc = WOUND_ACCENT[w.woundType] ?? Colors.primary;
              const isActive = idx === activeIndex;
              return (
                <TouchableOpacity
                  key={w.id}
                  style={[
                    styles.woundTab,
                    isActive && { backgroundColor: acc + '18', borderColor: acc },
                  ]}
                  onPress={() => setActiveIndex(idx)}
                  activeOpacity={0.75}
                >
                  <Text
                    style={[
                      styles.woundTabText,
                      isActive && { color: acc, fontWeight: '700' },
                    ]}
                  >
                    {w.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        )}

        {/* ③ Medical Scan Card */}
        {activeWound && <WoundScanCard wound={activeWound} />}

        {/* ④ Thời gian hồi phục */}
        {activeWound && <RecoveryCard recoveryTime={activeWound.recoveryTime} />}

        {/* ⑤ Quy trình sơ cứu */}
        {activeWound && activeWound.firstAid.length > 0 && (
          <>
            <View style={styles.firstAidSectionHeader}>
              <View style={styles.firstAidSectionIconWrap}>
                <Feather name="heart" size={16} color={Colors.primary} />
              </View>
              <Text style={styles.firstAidSectionTitle}>Quy trình sơ cứu</Text>
            </View>

            {activeWound.isFallback && (
              <View style={styles.fallbackAlert}>
                <Text style={styles.fallbackAlertIcon}>⚠️</Text>
                <Text style={styles.fallbackAlertText}>
                  Hệ thống AI đang có lượng truy cập cao. Dưới đây là phác đồ sơ cứu tiêu chuẩn từ Từ điển Y khoa SkinAid dựa trên mức độ vết thương của bạn.
                </Text>
              </View>
            )}

            {activeWound.firstAid.map((section, idx) => (
              <FirstAidSectionCard key={idx} section={section} />
            ))}
          </>
        )}

        {/* ⑥ Summary chip nếu nhiều vết */}
        {wounds.length > 1 && (
          <View style={styles.summaryBanner}>
            <Feather name="layers" size={14} color={Colors.primary} style={{ marginRight: 6 }} />
            <Text style={styles.summaryBannerText}>
              Xem thêm{' '}
              <Text style={styles.summaryBannerBold}>{wounds.length - 1}</Text>
              {' '}vết thương khác bằng cách nhấn vào tab phía trên.
            </Text>
          </View>
        )}
      </Animated.ScrollView>

      {/* ── Bottom bar ────────────────────────────────────────── */}
      <View style={[styles.bottomBar, { paddingBottom: Math.max(insets.bottom, 16) }]}>
        <TouchableOpacity
          style={styles.chatBtn}
          onPress={() => router.push({ pathname: '/chat', params: { analysisId } })}
          activeOpacity={0.8}
        >
          <Image
            source={require('../assets/logo_DermAid.png')}
            style={styles.dermAidBtnIcon}
          />
          <Text style={styles.chatBtnText}>Hỏi DermAid</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.homeBtn}
          onPress={() => router.replace('/(tabs)/home')}
          activeOpacity={0.85}
        >
          <LinearGradient
            colors={[Colors.primary, Colors.primaryDark]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.homeBtnGradient}
          >
            <Feather name="home" size={17} color="#fff" />
            <Text style={styles.homeBtnText}>Về trang chủ</Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ─── Styles ─────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: Colors.backgroundSecondary,
  },

  // ── Top bar ──
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
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: Colors.white,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 6,
    elevation: 2,
  },
  topBarCenter: {
    flex: 1,
    alignItems: 'center',
  },
  topBarTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: Colors.primary,
    letterSpacing: 1.5,
  },
  topBarSubtitle: {
    fontSize: 11,
    color: Colors.textMuted,
    marginTop: 1,
  },
  topBarSpacer: { width: 38 },
  shareBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: Colors.white,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 6,
    elevation: 2,
  },

  // ── Scroll ──
  scroll: { flex: 1 },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 16,
    gap: 14,
  },

  // ── Medical Disclaimer (at TOP) ──
  disclaimerCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    backgroundColor: '#FFFBEB',
    borderWidth: 1.5,
    borderColor: '#FDE68A',
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 14,
    shadowColor: '#F59E0B',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 3,
  },
  disclaimerIcon: { marginTop: 1, flexShrink: 0 },
  disclaimerBody: { flex: 1, gap: 4 },
  disclaimerTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#92400E',
    letterSpacing: 0.2,
  },
  disclaimerText: {
    fontSize: 12.5,
    color: '#78350F',
    lineHeight: 19,
  },
  disclaimerBold: {
    fontWeight: '700',
    color: '#92400E',
  },

  // ── Wound selector tabs ──
  woundTabRow: {
    gap: 8,
    paddingVertical: 2,
    paddingHorizontal: 2,
  },
  woundTab: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: Colors.borderLight,
    backgroundColor: Colors.backgroundTertiary,
  },
  woundTabDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
  },
  woundTabText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textLight,
  },

  // ── Medical Scan Card ──
  scanCard: {
    backgroundColor: Colors.white,
    borderRadius: 18,
    overflow: 'hidden',
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 5,
  },
  scanImageZone: {
    width: '100%',
    height: 220,
    backgroundColor: '#0F1923',
    position: 'relative',
    overflow: 'hidden',
  },
  scanImagePlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0F1923',
    gap: 8,
  },
  scanGrid: { ...StyleSheet.absoluteFillObject },
  scanGridH: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 1,
    backgroundColor: 'rgba(2,161,141,0.09)',
  },
  scanGridV: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    width: 1,
    backgroundColor: 'rgba(2,161,141,0.09)',
  },
  scanPlaceholderTxt: {
    fontSize: 11,
    color: 'rgba(2,161,141,0.45)',
    letterSpacing: 2,
  },
  corner: {
    position: 'absolute',
    width: 12,
    height: 12,
    borderColor: Colors.primary,
  },
  cornerTL: { top: -1, left: -1, borderTopWidth: 3, borderLeftWidth: 3, borderTopLeftRadius: 4 },
  cornerTR: { top: -1, right: -1, borderTopWidth: 3, borderRightWidth: 3, borderTopRightRadius: 4 },
  cornerBL: { bottom: -1, left: -1, borderBottomWidth: 3, borderLeftWidth: 3, borderBottomLeftRadius: 4 },
  cornerBR: { bottom: -1, right: -1, borderBottomWidth: 3, borderRightWidth: 3, borderBottomRightRadius: 4 },
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
    width: 6, height: 6, borderRadius: 3, backgroundColor: Colors.primary,
  },
  aiChipTxt: {
    fontSize: 10, fontWeight: '700', color: Colors.primary, letterSpacing: 0.5,
  },
  scanGradient: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 16,
    paddingBottom: 14,
    paddingTop: 40,
    gap: 2,
  },
  scanTypeLabel: {
    fontSize: 9,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.7)',
    letterSpacing: 1.5,
  },
  scanWoundLabel: {
    fontSize: 20,
    fontWeight: '800',
    color: '#fff',
    letterSpacing: 0.3,
  },
  scanInfoPanel: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    gap: 12,
  },
  scanInfoLeft: { flex: 1, gap: 5 },
  scanInfoCaption: {
    fontSize: 9,
    fontWeight: '700',
    color: Colors.textMuted,
    letterSpacing: 1.2,
  },
  scanAccuracyVal: {
    fontSize: 22,
    fontWeight: '800',
    color: Colors.primary,
    marginTop: -2,
  },
  scanAccuracyTrack: {
    height: 5,
    backgroundColor: Colors.backgroundTertiary,
    borderRadius: 10,
    overflow: 'hidden',
  },
  scanAccuracyFill: {
    height: '100%',
    borderRadius: 10,
  },
  scanInfoDivider: {
    width: 1,
    height: 54,
    backgroundColor: Colors.borderLight,
  },
  scanInfoRight: { flex: 1, gap: 5, alignItems: 'flex-start' },
  scanSeverityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    borderWidth: 1.5,
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  scanSeverityDot: { width: 7, height: 7, borderRadius: 4 },
  scanSeverityText: { fontSize: 12, fontWeight: '700' },
  scanNoSeverityText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textLight,
  },
  scanSeverityNote: {
    fontSize: 10,
    color: Colors.textMuted,
    fontWeight: '500',
    marginTop: 2,
  },

  // ── Recovery card ──
  recoveryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    backgroundColor: Colors.white,
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 14,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  recoveryIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  recoveryInfo: { flex: 1, gap: 3 },
  recoveryLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textMuted,
    letterSpacing: 0.3,
  },
  recoveryValue: {
    fontSize: 16,
    fontWeight: '800',
    color: Colors.primary,
  },

  // ── First aid section header ──
  firstAidSectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 4,
    marginBottom: -4,
  },
  firstAidSectionIconWrap: {
    width: 30,
    height: 30,
    borderRadius: 10,
    backgroundColor: Colors.primary + '15',
    alignItems: 'center',
    justifyContent: 'center',
  },
  firstAidSectionTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  fallbackAlert: {
    flexDirection: 'row',
    backgroundColor: '#FFFBEB',
    borderWidth: 1,
    borderColor: '#FCD34D',
    borderRadius: 12,
    padding: 12,
    marginTop: 6,
    alignItems: 'flex-start',
    gap: 8,
  },
  fallbackAlertIcon: {
    fontSize: 18,
    marginTop: -2,
  },
  fallbackAlertText: {
    flex: 1,
    fontSize: 13,
    color: '#92400E',
    lineHeight: 18,
  },

  // ── First aid group ──
  firstAidGroup: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  firstAidHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 12,
    gap: 10,
  },
  firstAidIconBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  firstAidIconChar: {
    fontSize: 15,
    fontWeight: '900',
    color: '#fff',
  },
  firstAidHeaderText: { flex: 1, gap: 1 },
  firstAidTitle: { fontSize: 14, fontWeight: '700' },
  firstAidTag: { fontSize: 9.5, fontWeight: '700', letterSpacing: 0.8 },
  firstAidStepCount: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 20,
  },
  firstAidStepCountNum: { fontSize: 12, fontWeight: '800', color: '#fff' },
  firstAidStepCountLabel: { fontSize: 9, fontWeight: '700', color: 'rgba(255,255,255,0.8)' },

  // ── Timeline ──
  timelineWrap: { paddingHorizontal: 14, paddingVertical: 10 },
  timelineRow: { flexDirection: 'row', gap: 12 },
  timelineLeft: { alignItems: 'center', width: 28 },
  timelineCircle: {
    width: 26,
    height: 26,
    borderRadius: 13,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  timelineNum: { fontSize: 11, fontWeight: '800' },
  timelineLine: { width: 1.5, flex: 1, marginTop: 4, marginBottom: 4 },
  timelineContent: {
    flex: 1,
    paddingBottom: 14,
    paddingTop: 3,
  },
  timelineContentLast: { paddingBottom: 4 },
  timelineText: {
    fontSize: 13.5,
    color: Colors.textPrimary,
    lineHeight: 20,
  },

  // ── Summary banner ──
  summaryBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.primary + '10',
    borderWidth: 1,
    borderColor: Colors.primary + '30',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  summaryBannerText: {
    flex: 1,
    fontSize: 12.5,
    color: Colors.textLight,
    lineHeight: 18,
  },
  summaryBannerBold: {
    fontWeight: '800',
    color: Colors.primary,
  },

  // ── Bottom bar ──
  bottomBar: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 16,
    paddingTop: 12,
    backgroundColor: Colors.white,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.07,
    shadowRadius: 12,
    elevation: 12,
  },
  chatBtn: {
    flex: 1.1,
    height: 52,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: Colors.primary,
    backgroundColor: Colors.white,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
    gap: 7,
  },
  dermAidBtnIcon: {
    width: 24,
    height: 24,
    borderRadius: 12,
  },
  chatBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.primary,
  },
  homeBtn: {
    flex: 1.6,
    height: 52,
    borderRadius: 14,
    overflow: 'hidden',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 12,
    elevation: 6,
  },
  homeBtnGradient: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: 14,
  },
  homeBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#fff',
    letterSpacing: 0.3,
  },

  // ── Empty / not found ──
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 14,
    paddingHorizontal: 32,
  },
  emptyText: {
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
});
