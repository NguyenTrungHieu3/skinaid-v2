// app/(tabs)/home.tsx
import { useNavigation } from "@react-navigation/native";
import { router } from "expo-router";
import React, { useCallback, useEffect, useState } from "react";
import {
  BackHandler,
  Image,
  ImageBackground,
  Modal,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "../../context/AuthContext";
import { useTabBarHeight } from "./_layout";

import ChatBubble from "../../components/home/ChatBubble";
import HomeHeader from "../../components/home/HomeHeader";
import { getAnalysisHistory, getAnalysisDetail, mapWoundLabel } from "../../services/woundService";
import { notificationService } from "../../services/notificationService";
import { useFocusEffect } from "@react-navigation/native";

const BACKEND_URL = "http://52.20.177.68";

// ─── Style tokens ───────────────────────────────────────────
const COLORS = {
  screenBg: "#F2F5F3",
  primary: "#1A7A5E",
  primaryLight: "#2a9f84ff",
  cardBg: "#FFFFFF",
  dark: "#1A1A1A",
  grey: "#8E8E93",
  iconBg: "#E8F5F0",
};

const RADIUS = 16;
const H_PAD = 16;

// ─── Hardcoded data ─────────────────────────────────────────
const SERVICES = [
  {
    emoji: "🩹",
    label: "Danh mục\nvết thương",
    key: "wound-categories",
    iconBg: "#FAECE7",
    tag: "6 loại",
    tagBg: "#FAECE7",
    tagColor: "#993C1D",
  },
  {
    emoji: "🧰",
    label: "Cẩm nang\nsơ cứu",
    key: "firstaid",
    iconBg: "#FAEEDA",
    tag: "Hướng dẫn",
    tagBg: "#FAEEDA",
    tagColor: "#854F0B",
  },
  {
    emoji: "📚",
    label: "Kiến thức\nda liễu",
    key: "knowledge",
    iconBg: "#EEEDFE",
    tag: "Bài viết",
    tagBg: "#EEEDFE",
    tagColor: "#534AB7",
  },
];

// Helper type for Home Activities
type HomeActivity = {
  id: string;
  wounds: { label: string; accuracy: number }[];
  date: string;
  imageUri?: string;
};

// Helper: lấy tất cả các nhãn vết thương trong 1 bản ghi
function getWoundLabels(wounds: HomeActivity['wounds']): string {
  if (!wounds || wounds.length === 0) return "Chưa phát hiện";
  return wounds.map((w) => w.label).join(', ');
}

// Helper: lấy độ chính xác trung bình
function getAvgAccuracy(wounds: HomeActivity['wounds']): number {
  if (!wounds || wounds.length === 0) return 0;
  const sum = wounds.reduce((acc, w) => acc + w.accuracy, 0);
  return Math.round(sum / wounds.length);
}

// Màu placeholder theo vị trí
const ACTIVITY_COLORS = ['#D4A090', '#8BAFC4', '#A8B4C4'];

const ARTICLES = [
  {
    key: "1",
    articleId: "skincare-morning",
    tag: "LÀM ĐẸP",
    title: "5 thói quen giúp da luôn sáng khỏe mỗi sáng",
    image: require("../../assets/kt_mh/kt1-overview.png"),
  },
  {
    key: "2",
    articleId: "wound-treatment",
    tag: "Y TẾ",
    title: "Quy trình xử lý vết thương đúng chuẩn",
    image: require("../../assets/kt_mh/kt2-overview.jpg"),
  },
  {
    key: "3",
    articleId: "burn-firstaid",
    tag: "SƠ CỨU",
    title: "Cách sơ cứu bỏng tại nhà an toàn và hiệu quả",
    image: require("../../assets/kt_mh/kt3-overview.png"),
  },
  {
    key: "4",
    articleId: "eczema-signs",
    tag: "DA LIỄU",
    title: "Nhận biết sớm các dấu hiệu viêm da cơ địa",
    image: require("../../assets/kt_mh/kt4-overview.png"),
  },
  {
    key: "5",
    articleId: "skin-foods",
    tag: "DINH DƯỠNG",
    title: "10 loại thực phẩm tốt cho làn da từ bên trong",
    image: require("../../assets/kt_mh/kt5-overview.png"),
  },
];

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const tabBarHeight = useTabBarHeight();
  const navigation = useNavigation();
  const { signOut } = useAuth();
  const [showLogoutModal, setShowLogoutModal] = useState(false);

  // Bắt nút Back Android — hiện modal xác nhận thay vì thoát thẳng
  useEffect(() => {
    const sub = BackHandler.addEventListener("hardwareBackPress", () => {
      setShowLogoutModal(true);
      return true; // chặn hành vi mặc định
    });
    return () => sub.remove();
  }, []);

  // Fetch API activities cho trang chủ (latest 3)
  const [recentActivities, setRecentActivities] = useState<HomeActivity[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const { token } = useAuth();
  
  const fetchRecent = async () => {
    try {
      // Gọi cả 2 API cùng lúc
      const [res, notiRes] = await Promise.all([
        getAnalysisHistory(3, 0),
        notificationService.getNotifications(1).catch(() => ({ unread_count: 0 }))
      ]);

      setUnreadCount((notiRes as any).unread_count || 0);

      const events = res.events || [];
      
      const mapped = await Promise.all(
        events.map(async (event) => {
          let detail = null;
          try {
            detail = await getAnalysisDetail(event.analysis_id);
          } catch (e) {
            console.log("Error detail home", e);
          }
          
          const d = new Date(event.analyzed_at);
          const dateStr = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;

          const wounds: { label: string; accuracy: number }[] = [];
          if (detail && detail.significant_wounds) {
            detail.significant_wounds.forEach(w => {
              wounds.push({
                label: mapWoundLabel(w.wound_type),
                accuracy: Math.round((w.confidence_score || 0.85) * 100)
              });
            });
          }

          const imgUrl = event.image_url?.startsWith("http") ? event.image_url : BACKEND_URL + event.image_url;

          return {
            id: event.analysis_id,
            date: dateStr,
            wounds,
            imageUri: event.image_url ? imgUrl : undefined
          } as HomeActivity;
        })
      );
      setRecentActivities(mapped);
    } catch (e) {
      console.log("Failed to fetch recent home", e);
    }
  };

  useFocusEffect(
    useCallback(() => {
      fetchRecent();
    }, [token])
  );

  const handleConfirmLogout = useCallback(async () => {
    setShowLogoutModal(false);
    await signOut();
    router.replace("../(auth)/sign-in");
  }, [signOut]);

  const handleScan = () => {
    router.push("/(tabs)/scan");
  };

  return (
    <View style={styles.container}>
      {/* ── Logout Confirmation Modal ── */}
      <Modal
        visible={showLogoutModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowLogoutModal(false)}
      >
        <Pressable
          style={styles.modalOverlay}
          onPress={() => setShowLogoutModal(false)}
        >
          <Pressable style={styles.modalCard} onPress={() => {}}>
            <Text style={styles.modalTitle}>Đăng xuất</Text>
            <Text style={styles.modalMessage}>
              Bạn có muốn đăng xuất khỏi tài khoản không?
            </Text>
            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.modalBtnCancel}
                activeOpacity={0.75}
                onPress={() => setShowLogoutModal(false)}
              >
                <Text style={styles.modalBtnCancelText}>Hủy bỏ</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.modalBtnConfirm}
                activeOpacity={0.8}
                onPress={handleConfirmLogout}
              >
                <Text style={styles.modalBtnConfirmText}>Đồng ý</Text>
              </TouchableOpacity>
            </View>
          </Pressable>
        </Pressable>
      </Modal>
      <StatusBar
        barStyle="dark-content"
        translucent
        backgroundColor="transparent"
      />

      {/* ── HEADER — preserved as-is ── */}
      <View style={[styles.topBarWrapper, { paddingTop: insets.top }]}>
        <HomeHeader
          unreadCount={unreadCount}
          onPressNotification={() => router.push("/notifications")}
          onPressProfile={() => router.push("./(tabs)/profile")}
        />
      </View>

      {/* ── SCROLLABLE BODY ── */}
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={{
          paddingHorizontal: H_PAD,
          paddingTop: 16,
          paddingBottom: tabBarHeight + 20,
        }}
        showsVerticalScrollIndicator={false}
      >
        {/* ════════════════════════════════════════════════════
            SECTION 1 — Hero Banner Card
           ════════════════════════════════════════════════════ */}
        <ImageBackground
          source={require("../../assets/banner-1.jpeg")}
          style={styles.heroBanner}
          imageStyle={styles.heroBannerImage}
          resizeMode="cover"
        >
          <View style={styles.heroBannerOverlay}>
            <Text style={styles.heroTitle}>
              Phân tích vết thương{"\n"}bằng AI
            </Text>
            <Text style={styles.heroSubtitle}>
              Nhận diện và chẩn đoán 6 loại vết thương phổ biến với kết quả nhanh chóng, chính xác.
            </Text>
            <TouchableOpacity style={styles.heroButton} onPress={handleScan}>
              <Text style={styles.heroButtonText}>Bắt đầu ngay →</Text>
            </TouchableOpacity>
          </View>
        </ImageBackground>

        {/* ════════════════════════════════════════════════════
            SECTION 2 — Dịch vụ y tế  (3-col + guide)
           ════════════════════════════════════════════════════ */}
        <View style={styles.svcSectionHeader}>
          <Text style={styles.svcSectionTitle}>Dịch vụ y tế</Text>
          <TouchableOpacity activeOpacity={0.6} onPress={() => console.log("Xem thêm dịch vụ")}>
            <Text style={styles.svcSectionLink}>Xem thêm</Text>
          </TouchableOpacity>
        </View>

        {/* ── Tier 1: 3-column cards ── */}
        <View style={styles.svcRow}>
          {SERVICES.map((svc) => (
            <Pressable
              key={svc.key}
              style={({ pressed }) => [
                styles.svcCard,
                pressed && { opacity: 0.7 },
              ]}
              onPress={() => router.push(`/${svc.key}` as any)}
            >
              <View style={[styles.svcIconBox, { backgroundColor: svc.iconBg }]}>
                <Text style={styles.svcEmoji}>{svc.emoji}</Text>
              </View>
              <Text style={styles.svcLabel}>{svc.label}</Text>
              <Text
                style={[
                  styles.svcTag,
                  { backgroundColor: svc.tagBg, color: svc.tagColor },
                ]}
              >
                {svc.tag}
              </Text>
            </Pressable>
          ))}
        </View>

        {/* ── Tier 2: Guide button ── */}
        <Pressable
          style={({ pressed }) => [
            styles.guideBtn,
            pressed && { opacity: 0.7 },
          ]}
          onPress={() => (navigation as any)?.navigate?.("AppGuide")}
        >
          <View style={styles.guideBtnLeft}>
            <View style={styles.guideBtnIcon}>
              <Text style={{ fontSize: 18 }}>📖</Text>
            </View>
            <View>
              <Text style={styles.guideBtnTitle}>Hướng dẫn sử dụng app</Text>
              <Text style={styles.guideBtnSub}>Bắt đầu nhanh trong 2 phút</Text>
            </View>
          </View>
          <View style={styles.guideBtnArrow}>
            <Text style={{ fontSize: 16, color: '#1A7A5E',bottom: 2}}>›</Text>
          </View>
        </Pressable>

        {/* ════════════════════════════════════════════════════
            SECTION 3 — Hoạt động gần đây
           ════════════════════════════════════════════════════ */}
        <View style={styles.activityCard}>
          {/* Header row */}
          <View style={styles.activityHeader}>
            <Text style={styles.activityHeaderLabel}>HOẠT ĐỘNG GẦN ĐÂY</Text>
            <TouchableOpacity
              activeOpacity={0.7}
              onPress={() => router.push('/(tabs)/history')}
            >
              <Text style={styles.activityHeaderLink}>Tất cả lịch sử</Text>
            </TouchableOpacity>
          </View>

          {recentActivities.map((item, index) => (
            <React.Fragment key={item.id}>
              {index > 0 && <View style={styles.activityDivider} />}
              <TouchableOpacity
                style={styles.activityRow}
                activeOpacity={0.75}
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                onPress={() => router.push({ pathname: '/history-detail' as any, params: { analysisId: item.id } })}
              >
                {item.imageUri ? (
                  <Image source={{ uri: item.imageUri }} style={styles.activityImage} resizeMode="cover" />
                ) : (
                  <View style={[styles.activityImage, { backgroundColor: ACTIVITY_COLORS[index % ACTIVITY_COLORS.length] }]} />
                )}
                <View style={styles.activityTextCol}>
                  <Text style={styles.activityTitle}>{getWoundLabels(item.wounds)}</Text>
                  <Text style={styles.activitySubtitle}>
                    ✅ {getAvgAccuracy(item.wounds)}% chính xác • {item.date}
                  </Text>
                </View>
                <Text style={styles.activityChevron}>›</Text>
              </TouchableOpacity>
            </React.Fragment>
          ))}
        </View>

        {/* ════════════════════════════════════════════════════
            SECTION 4 — Kiến thức & Mẹo hay
           ════════════════════════════════════════════════════ */}
        <Text style={styles.sectionTitle}>Kiến thức & Mẹo hay</Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.articlesRow}
        >
          {ARTICLES.map((article) => (
            <TouchableOpacity
              key={article.key}
              style={styles.articleCard}
              activeOpacity={0.8}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              onPress={() => router.push({ pathname: '/knowledge-detail' as any, params: { articleId: article.articleId } })}
            >
              <Image
                source={article.image}
                style={styles.articleImage}
                resizeMode="cover"
              />
              <View style={styles.articleBody}>
                <Text style={styles.articleTag}>{article.tag}</Text>
                <Text style={styles.articleTitle}>{article.title}</Text>
              </View>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </ScrollView>

      {/* ── DermAid floating chat bubble ── */}
      <ChatBubble bottomOffset={tabBarHeight + 20} />
    </View>
  );
}

// ─── Styles ─────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.screenBg,
  },
  topBarWrapper: {
    backgroundColor: "#FFFFFF",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  scrollView: {
    flex: 1,
  },

  // ── Section Title ──
  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: COLORS.dark,
    marginBottom: 12,
  },

  // ── SECTION 1 — Hero Banner ──
  heroBanner: {
    borderRadius: RADIUS,
    marginBottom: 24,
    overflow: "hidden",
  },
  heroBannerImage: {
    borderRadius: RADIUS,
  },
  heroBannerOverlay: {
    backgroundColor: "rgba(26, 122, 94, 0.48)",
    padding: 20,
  },
  heroTitle: {
    fontSize: 20,
    fontWeight: "800",
    color: "#FFFFFF",
    lineHeight: 28,
    marginBottom: 8,
  },
  heroSubtitle: {
    fontSize: 13,
    fontWeight: "400",
    color: "rgba(255,255,255,0.9)",
    lineHeight: 19,
    marginBottom: 16,
  },
  heroButton: {
    alignSelf: "flex-start",
    backgroundColor: "#FFFFFF",
    borderRadius: 50,
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  heroButtonText: {
    fontSize: 13,
    fontWeight: "700",
    color: COLORS.primaryLight,
  },

  // ── SECTION 2 — Dịch vụ y tế ──
  svcSectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 14,
  },
  svcSectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1A1A1A",
  },
  svcSectionLink: {
    fontSize: 13,
    color: "#1A7A5E",
  },
  svcRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 12,
  },
  svcCard: {
    flex: 1,
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    borderWidth: 0.5,
    borderColor: "#E0E0E0",
    paddingVertical: 16,
    paddingHorizontal: 8,
    alignItems: "center",
    gap: 8,
  },
  svcIconBox: {
    width: 46,
    height: 46,
    borderRadius: 13,
    alignItems: "center",
    justifyContent: "center",
  },
  svcEmoji: {
    fontSize: 22,
  },
  svcLabel: {
    fontSize: 11,
    fontWeight: "600",
    color: "#1A1A1A",
    textAlign: "center",
    lineHeight: 16,
  },
  svcTag: {
    fontSize: 10,
    borderRadius: 20,
    paddingHorizontal: 8,
    paddingVertical: 2,
    marginTop: -2,
    overflow: "hidden",
  },
  guideBtn: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    borderWidth: 1.5,
    borderStyle: "dashed",
    borderColor: "#B2D8CC",
    paddingVertical: 13,
    paddingHorizontal: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 24,
  },
  guideBtnLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  guideBtnIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: "#E1F5EE",
    alignItems: "center",
    justifyContent: "center",
  },
  guideBtnTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#1A7A5E",
  },
  guideBtnSub: {
    fontSize: 11,
    color: "#888888",
  },
  guideBtnArrow: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: "#E1F5EE",
    alignItems: "center",
    justifyContent: "center",
    
  },

  // ── SECTION 3 — Hoạt động gần đây ──
  activityCard: {
    backgroundColor: COLORS.cardBg,
    borderRadius: RADIUS,
    padding: 16,
    marginBottom: 24,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  activityHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 14,
  },
  activityHeaderLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: COLORS.primary,
    letterSpacing: 1,
  },
  activityHeaderLink: {
    fontSize: 13,
    fontWeight: "600",
    color: COLORS.primary,
  },
  activityRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  activityImage: {
    width: 52,
    height: 52,
    borderRadius: 10,
    backgroundColor: "#C49A8A",
  },
  activityTextCol: {
    flex: 1,
    marginLeft: 12,
  },
  activityTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: COLORS.dark,
    marginBottom: 3,
  },
  activitySubtitle: {
    fontSize: 12,
    fontWeight: "400",
    color: COLORS.grey,
  },
  activityChevron: {
    fontSize: 22,
    color: COLORS.grey,
    marginLeft: 8,
  },
  activityDivider: {
    height: 1,
    backgroundColor: "#F0F0F0",
    marginVertical: 10,
  },

  // ── SECTION 4 — Kiến thức & Mẹo hay ──
  articlesRow: {
    gap: 12,
    paddingBottom: 8,
  },
  articleCard: {
    width: 160,
    borderRadius: RADIUS,
    backgroundColor: COLORS.cardBg,
    overflow: "hidden",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  articleImage: {
    height: 100,
    width: "100%",
  },
  articleBody: {
    padding: 10,
  },
  articleTag: {
    fontSize: 10,
    fontWeight: "600",
    color: COLORS.grey,
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  articleTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: COLORS.dark,
    lineHeight: 18,
  },

  // ── Logout Confirmation Modal ────────────────────────
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.4)",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 40,
  },
  modalCard: {
    width: "100%",
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    paddingVertical: 24,
    paddingHorizontal: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 8,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1A1A1A",
    marginBottom: 8,
  },
  modalMessage: {
    fontSize: 14,
    color: "#555555",
    lineHeight: 20,
    marginBottom: 20,
  },
  modalActions: {
    flexDirection: "row",
    gap: 10,
    justifyContent: "flex-end",
  },
  modalBtnCancel: {
    paddingVertical: 9,
    paddingHorizontal: 18,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: "#D0D0D0",
    backgroundColor: "#F5F5F5",
  },
  modalBtnCancelText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#555555",
  },
  modalBtnConfirm: {
    paddingVertical: 9,
    paddingHorizontal: 18,
    borderRadius: 10,
    backgroundColor: COLORS.primary,
  },
  modalBtnConfirmText: {
    fontSize: 14,
    fontWeight: "700",
    color: "#FFFFFF",
  },
});
