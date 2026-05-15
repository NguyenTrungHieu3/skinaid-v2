// app/(tabs)/history.tsx
import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  Image,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTabBarHeight } from "./_layout";
import { getAnalysisHistory, getAnalysisDetail, mapWoundLabel } from "../../services/woundService";
import { chatbotService } from "../../services/chatbotService";
import { useAuth } from "../../context/AuthContext";
import { useFocusEffect } from "@react-navigation/native";
import { useCallback } from "react";

// In-memory cache để không tải lại khi back
let globalHistoryCache: HistoryRecord[] | null = null;

// ─── Constants ───────────────────────────────────────────────
const TEAL = "#1A7A5E";
const BG = "#F2F5F3";
const BACKEND_URL = "https://skinaid.xyz";

// Hệ thống hỗ trợ 6 loại vết thương:
//   Có mức độ nghiêm trọng : Bỏng | Bầm | Trầy | Mụn trứng cá
//   Không có mức độ        : Vảy nến | Nấm da
const SEVERITY_CONFIG: Record<
  string,
  { label: string; bg: string; color: string }
> = {
  NHE:       { label: "NHẸ",        bg: "#DCFCE7", color: "#166534" },
  TRUNG_BINH:{ label: "TRUNG BÌNH", bg: "#FEF9C3", color: "#854D0E" },
  NANG:      { label: "NẶNG",       bg: "#FEE2E2", color: "#991B1B" },
};

// ─── Filter Options ───────────────────────────────────────────
type FilterKey = "all" | "1d" | "3d" | "7d" | "1m";

const FILTER_OPTIONS: { key: FilterKey; label: string; days: number | null }[] = [
  { key: "all", label: "Tất cả",  days: null },
  { key: "1d",  label: "1 ngày",  days: 1    },
  { key: "3d",  label: "3 ngày",  days: 3    },
  { key: "7d",  label: "7 ngày",  days: 7    },
  { key: "1m",  label: "1 tháng", days: 30   },
];

// ─── Types ───────────────────────────────────────────────────
type Wound = {
  title: string;
  severity?: keyof typeof SEVERITY_CONFIG;
  recoveryDays: string;
  accuracy: number;
  criticalNote?: string;
};

type HistoryRecord = {
  id: string;
  date: string;
  imageUri?: string;
  bgColor?: string;
  wounds: Wound[];
};

type MonthGroup = {
  month: string;
  records: HistoryRecord[];
};

// ─── Helpers ─────────────────────────────────────────────────
/** Parse date string: "dd/MM/yyyy HH:mm:ss" → Date */
function parseDate(dateStr: string): Date {
  const [datePart, timePart] = dateStr.split(" ");
  if (!datePart) return new Date();
  const [d, m, y] = datePart.split("/").map(Number);
  const [hh, mm, ss] = (timePart ?? "00:00:00").split(":").map(Number);
  return new Date(y, m - 1, d, hh, mm, ss);
}

/** Lọc record theo khoảng thời gian tính từ hiện tại */
function isWithinDays(dateStr: string, days: number): boolean {
  const recordDate = parseDate(dateStr);
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  cutoff.setHours(0, 0, 0, 0);
  return recordDate >= cutoff;
}

/** Nhóm records theo tháng (động, không hardcode) */
function groupByMonth(records: HistoryRecord[]): MonthGroup[] {
  const map = new Map<string, HistoryRecord[]>();
  records.forEach((rec) => {
    const d = parseDate(rec.date);
    const key = `THÁNG ${d.getMonth() + 1}, ${d.getFullYear()}`;
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(rec);
  });
  return Array.from(map.entries()).map(([month, recs]) => ({
    month,
    records: recs,
  }));
}

// ─── Sub-components ──────────────────────────────────────────
function SeverityBadge({
  severity,
}: {
  severity?: keyof typeof SEVERITY_CONFIG;
}) {
  if (!severity) return null;
  const cfg = SEVERITY_CONFIG[severity];
  return (
    <View style={[styles.badge, { backgroundColor: cfg.bg }]}>
      <Text style={[styles.badgeText, { color: cfg.color }]}>{cfg.label}</Text>
    </View>
  );
}

function WoundRow({ wound, isLast }: { wound: Wound; isLast: boolean }) {
  const accuracyColor =
    wound.accuracy >= 95 ? TEAL : wound.accuracy >= 85 ? "#D97706" : "#EF4444";

  return (
    <View style={[styles.woundRow, !isLast && styles.woundRowDivider]}>
      <View style={styles.woundTitleRow}>
        <Text style={styles.woundTitle}>{wound.title}</Text>
        <Text style={[styles.accuracyText, { color: accuracyColor }]}>
          {wound.accuracy}%
        </Text>
      </View>

      {wound.criticalNote ? (
        <Text style={styles.criticalNote}>{wound.criticalNote}</Text>
      ) : null}

      <View style={styles.woundMeta}>
        <SeverityBadge severity={wound.severity} />
        <View style={styles.recoveryRow}>
          <Feather name="calendar" size={11} color="#9CA3AF" />
          <Text style={styles.recoveryText}>{wound.recoveryDays}</Text>
        </View>
      </View>
    </View>
  );
}

function RecordCard({ record }: { record: HistoryRecord }) {
  const isMulti = record.wounds.length > 1;
  const placeholderBg = record.bgColor ?? "#D1D5DB";

  const handlePress = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    router.push({ pathname: '/history-detail' as any, params: { analysisId: record.id } });
  };

  return (
    <TouchableOpacity style={styles.card} activeOpacity={0.85} onPress={handlePress}>
      {/* ── Container ảnh — luôn fit full chiều cao card ── */}
      <View style={styles.cardImageContainer}>
        {record.imageUri ? (
          <Image
            source={{ uri: record.imageUri }}
            style={styles.cardImageFull}
            resizeMode="cover"
          />
        ) : (
          <View
            style={[
              styles.cardImageFull,
              styles.cardImagePlaceholder,
              { backgroundColor: placeholderBg },
            ]}
          >
            <Feather name="camera" size={22} color="rgba(255,255,255,0.8)" />
          </View>
        )}
      </View>

      {/* ── Nội dung ── */}
      <View style={styles.cardBody}>
        <Text style={styles.cardDate}>{record.date}</Text>

        {isMulti && (
          <View style={styles.woundCountBadge}>
            <Feather name="layers" size={12} color={TEAL} />
            <Text style={styles.woundCountText}>
              {record.wounds.length} vết thương đã được nhận diện
            </Text>
          </View>
        )}

        {record.wounds.map((w, idx) => (
          <WoundRow
            key={idx}
            wound={w}
            isLast={idx === record.wounds.length - 1}
          />
        ))}
      </View>
    </TouchableOpacity>
  );
}

// ─── Main Screen ─────────────────────────────────────────────
export default function HistoryScreen() {
  const insets = useSafeAreaInsets();
  const tabBarHeight = useTabBarHeight();
  const { token } = useAuth();
  
  const [historyRecords, setHistoryRecords] = useState<HistoryRecord[]>(globalHistoryCache || []);
  const [isLoading, setIsLoading] = useState(!globalHistoryCache);

  const [query, setQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterKey>("all");
  const [showFilterMenu, setShowFilterMenu] = useState(false);

  const fetchData = async (silent = false) => {
    try {
      if (!silent) setIsLoading(true);
      // Lấy danh sách metadata từ API
      const resHistory = await getAnalysisHistory(25, 0);
      const events = resHistory.events || [];

      // Fetch song song detail cho tất cả item nhìn thấy (tránh chập delay)
      const mappedResults = await Promise.all(
        events.map(async (event) => {
          let detail = null;
          try {
            detail = await getAnalysisDetail(event.analysis_id);
          } catch (e) {
            console.log("Error fetching detail for", event.analysis_id);
          }
          
          const d = new Date(event.analyzed_at);
          const dateStr = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`;

          const wounds: Wound[] = [];
          if (detail && detail.significant_wounds) {
            detail.significant_wounds.forEach((apiWound) => {
              const severityValue = apiWound.severity;
              const isChronic = ["psoriasis", "fungal", "acne"].includes(apiWound.wound_type);
              
              let sevKey: keyof typeof SEVERITY_CONFIG | undefined = undefined;
              if (!isChronic) {
                 sevKey = severityValue === "severe" ? "NANG" : severityValue === "moderate" ? "TRUNG_BINH" : "NHE";
              }

              wounds.push({
                title: mapWoundLabel(apiWound.wound_type),
                severity: sevKey,
                recoveryDays: apiWound.firstaid_snapshot?.estimated_healing_time || "Cần điều trị theo chỉ dẫn",
                accuracy: Math.round((apiWound.confidence_score || 0.85) * 100),
                criticalNote: severityValue === "severe" ? "CẦN CHĂM SÓC Y TẾ" : undefined,
              });
            });
          }

          const imgUrl = event.image_url.startsWith("http") ? event.image_url : BACKEND_URL + event.image_url;

          return {
            id: event.analysis_id,
            date: dateStr,
            imageUri: imgUrl,
            bgColor: "#E2E8F0",
            wounds,
          } as HistoryRecord;
        })
      );
      
      const res = mappedResults.filter(Boolean) as HistoryRecord[];
      globalHistoryCache = res;
      setHistoryRecords(res);
    } catch (e) {
      console.log("Failed to fetch history API", e);
    } finally {
      setIsLoading(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      // Nếu đã có cache thì fetch ngầm để update list (trường hợp vừa chụp ảnh xong)
      fetchData(!!globalHistoryCache);
    }, [token])
  );

  // 1. Lọc records theo thời gian + từ khoá tìm kiếm
  const filtered = historyRecords.filter((rec) => {
    const filterOpt = FILTER_OPTIONS.find((f) => f.key === activeFilter);
    const matchesDate =
      filterOpt?.days != null ? isWithinDays(rec.date, filterOpt.days) : true;

    const matchesQuery = query.trim()
      ? rec.wounds.some((w) =>
          w.title.toLowerCase().includes(query.toLowerCase())
        )
      : true;

    return matchesDate && matchesQuery;
  });

  // 2. Nhóm theo tháng (động)
  const groupedData = groupByMonth(filtered);

  const activeLabel =
    FILTER_OPTIONS.find((f) => f.key === activeFilter)?.label ?? "Tất cả";

  return (
    <View style={[styles.screen, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" backgroundColor={BG} />

      {/* ── Header ── */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Lịch sử</Text>
      </View>

      {/* ── Search + Filter ── */}
      <View style={styles.searchRow}>
        <View style={styles.searchBox}>
          <Feather
            name="search"
            size={16}
            color="#9CA3AF"
            style={{ marginRight: 8 }}
          />
          <TextInput
            style={styles.searchInput}
            placeholder="Tìm kiếm lịch sử..."
            placeholderTextColor="#9CA3AF"
            value={query}
            onChangeText={setQuery}
            returnKeyType="search"
          />
          {query.length > 0 && (
            <TouchableOpacity onPress={() => setQuery("")}>
              <Feather name="x" size={16} color="#9CA3AF" />
            </TouchableOpacity>
          )}
        </View>

        {/* Nút lọc + dropdown */}
        <View>
          <TouchableOpacity
            style={[styles.filterBtn, showFilterMenu && styles.filterBtnActive]}
            activeOpacity={0.8}
            onPress={() => setShowFilterMenu((v) => !v)}
          >
            <Feather name="sliders" size={18} color="#FFFFFF" />
          </TouchableOpacity>

          {showFilterMenu && (
            <>
              {/* Overlay — nhấn ngoài đóng menu */}
              <Pressable
                style={StyleSheet.absoluteFillObject}
                onPress={() => setShowFilterMenu(false)}
              />
              <View style={styles.filterDropdown}>
                {FILTER_OPTIONS.map((opt, idx) => (
                  <TouchableOpacity
                    key={opt.key}
                    style={[
                      styles.filterOption,
                      idx < FILTER_OPTIONS.length - 1 &&
                        styles.filterOptionBorder,
                      activeFilter === opt.key && styles.filterOptionActive,
                    ]}
                    onPress={() => {
                      setActiveFilter(opt.key);
                      setShowFilterMenu(false);
                    }}
                  >
                    <Text
                      style={[
                        styles.filterOptionText,
                        activeFilter === opt.key &&
                          styles.filterOptionTextActive,
                      ]}
                    >
                      {opt.label}
                    </Text>
                    {activeFilter === opt.key && (
                      <Feather name="check" size={13} color={TEAL} />
                    )}
                  </TouchableOpacity>
                ))}
              </View>
            </>
          )}
        </View>
      </View>

      {/* ── Chip hiển thị filter đang chọn (nếu khác "Tất cả") ── */}
      {activeFilter !== "all" && (
        <View style={styles.activeFilterChip}>
          <Feather name="clock" size={12} color={TEAL} />
          <Text style={styles.activeFilterChipText}>{activeLabel}</Text>
          <TouchableOpacity onPress={() => setActiveFilter("all")}>
            <Feather name="x" size={13} color={TEAL} />
          </TouchableOpacity>
        </View>
      )}

      {/* ── List ── */}
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{
          paddingHorizontal: 16,
          paddingBottom: tabBarHeight + 20,
          paddingTop: 4,
        }}
      >
        {isLoading ? (
          <View style={{ paddingVertical: 40, alignItems: "center" }}>
            <Text style={{ color: "#9CA3AF" }}>Đang tải lịch sử phân tích...</Text>
          </View>
        ) : groupedData.length === 0 ? (
          <View style={styles.emptyState}>
            <Feather name="inbox" size={40} color="#D1D5DB" />
            <Text style={styles.emptyText}>Không có kết quả</Text>
            <Text style={styles.emptySubText}>
              Thử thay đổi bộ lọc hoặc từ khoá tìm kiếm
            </Text>
          </View>
        ) : (
          groupedData.map((group) => (
            <View key={group.month}>
              <Text style={styles.monthLabel}>{group.month}</Text>
              {group.records.map((rec) => (
                <RecordCard key={rec.id} record={rec} />
              ))}
            </View>
          ))
        )}

        {/* Load more */}
        {/* <TouchableOpacity style={styles.loadMoreBtn} activeOpacity={0.7}>
          <Text style={styles.loadMoreText}>XEM CÁC PHÂN TÍCH TRƯỚC ĐÓ</Text>
        </TouchableOpacity> */}
      </ScrollView>
    </View>
  );
}

// ─── Styles ──────────────────────────────────────────────────
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: BG },

  header: { paddingHorizontal: 16, paddingVertical: 14 },
  headerTitle: { fontSize: 22, fontWeight: "700", color: "#1A1A1A" },

  // Search
  searchRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    gap: 10,
    marginBottom: 8,
  },
  searchBox: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  searchInput: { flex: 1, fontSize: 14, color: "#1A1A1A", padding: 0 },

  // Filter button
  filterBtn: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: TEAL,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: TEAL,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.35,
    shadowRadius: 6,
    elevation: 4,
  },
  filterBtnActive: { backgroundColor: "#145F49" },

  // Dropdown
  filterDropdown: {
    position: "absolute",
    top: 50,
    right: 0,
    width: 130,
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 12,
    elevation: 10,
    zIndex: 999,
    overflow: "hidden",
  },
  filterOption: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 11,
    paddingHorizontal: 14,
  },
  filterOptionBorder: {
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
  },
  filterOptionActive: { backgroundColor: "#F0FDF6" },
  filterOptionText: { fontSize: 13, color: "#374151", fontWeight: "500" },
  filterOptionTextActive: { color: TEAL, fontWeight: "700" },

  // Active filter chip
  activeFilterChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    alignSelf: "flex-start",
    marginHorizontal: 16,
    marginBottom: 8,
    backgroundColor: "#E8F5F0",
    borderRadius: 20,
    paddingVertical: 5,
    paddingHorizontal: 12,
  },
  activeFilterChipText: {
    fontSize: 12,
    fontWeight: "600",
    color: TEAL,
    flex: 1,
  },

  // Month label (động)
  monthLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: "#9CA3AF",
    letterSpacing: 0.8,
    marginBottom: 10,
    marginTop: 8,
  },

  // Card
  card: {
    flexDirection: "row",
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    marginBottom: 10,
    overflow: "hidden",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  cardImageContainer: { width: 88, alignSelf: "stretch" },
  cardImageFull: { flex: 1, minHeight: 88 },
  cardImagePlaceholder: { alignItems: "center", justifyContent: "center" },
  cardBody: { flex: 1, paddingHorizontal: 12, paddingTop: 10, paddingBottom: 12 },
  cardDate: { fontSize: 11, color: "#9CA3AF", marginBottom: 6 },

  // Multi-wound badge
  woundCountBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    backgroundColor: "#E8F5F0",
    borderRadius: 8,
    paddingVertical: 5,
    paddingHorizontal: 10,
    alignSelf: "flex-start",
    marginBottom: 8,
  },
  woundCountText: { fontSize: 11, fontWeight: "700", color: TEAL },

  // Wound row
  woundRow: { paddingBottom: 8 },
  woundRowDivider: {
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
    marginBottom: 8,
  },
  woundTitleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  woundTitle: { fontSize: 14, fontWeight: "700", color: "#1A1A1A", flex: 1 },
  accuracyText: { fontSize: 14, fontWeight: "800", marginLeft: 6 },
  criticalNote: {
    fontSize: 10,
    fontWeight: "700",
    color: "#EF4444",
    letterSpacing: 0.3,
    marginTop: 1,
    marginBottom: 2,
  },
  woundMeta: { flexDirection: "row", alignItems: "center", gap: 8, marginTop: 5 },

  // Badge
  badge: { borderRadius: 20, paddingHorizontal: 9, paddingVertical: 3 },
  badgeText: { fontSize: 10, fontWeight: "700" },

  // Recovery
  recoveryRow: { flexDirection: "row", alignItems: "center", gap: 4 },
  recoveryText: { fontSize: 11, color: "#6B7280" },

  // Empty state
  emptyState: { alignItems: "center", paddingVertical: 60, gap: 8 },
  emptyText: { fontSize: 15, fontWeight: "600", color: "#9CA3AF" },
  emptySubText: { fontSize: 12, color: "#B0B8C1", textAlign: "center" },

  // Load more
  loadMoreBtn: { alignItems: "center", paddingVertical: 20 },
  loadMoreText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#9CA3AF",
    letterSpacing: 0.5,
  },
});
