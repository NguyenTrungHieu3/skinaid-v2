import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import React from "react";
import {
  Image,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { Colors } from "../constants/colors";

// Dữ liệu nội dung danh mục
const WOUND_CATEGORIES = [
  {
    id: "tray-xuoc",
    title: "Trầy xước",
    english: "Abrasions",
    type: "Tổn thương vật lý",
    color: "#E25A3B", // Đỏ cam
    desc: "Tổn thương mất lớp biểu bì hoặc vài phần lớp bì do ma sát với bề mặt thô ráp. Thường ít chảy máu nhiều nhưng dễ nhiễm trùng bề mặt nếu không rửa sạch đất cát.",
    image: require("../assets/woundImage/trayXuoc.jpg"),
  },
  {
    id: "bam-tim",
    title: "Bầm tím",
    english: "Bruises / Contusions",
    type: "Tổn thương vật lý",
    color: "#5C4B99", // Tím
    desc: "Mạch máu nhỏ dưới da bị vỡ do va đập kín làm máu thoát ra mô xung quanh, gây đổi màu da từ đỏ sẫm sang tím, xanh và vàng trước khi mờ hẳn.",
    image: require("../assets/woundImage/bam.jpg"),
  },
  {
    id: "bong",
    title: "Bỏng",
    english: "Burns",
    type: "Tổn thương nhiệt",
    color: "#D97706", // Cam hổ phách
    desc: "Tổn thương mô do nhiệt, diện, hóa chất hoặc ma sát. Phân thành nhiều cấp độ tổn thương (I, II, III). Nguy cơ hoại tử, nhiễm trùng và mất nước rất cao.",
    image: require("../assets/woundImage/bong.jpg"),
  },
  {
    id: "mun-trung-ca",
    title: "Mụn trứng cá",
    english: "Acne Vulgaris",
    type: "Bệnh lý biểu bì",
    color: "#059669", // Xanh lục
    desc: "Tình trạng viêm nang lông tuyến bã do bít tắc lỗ chân lông. Phổ biến ở mặt, lưng có thể kèm mụn mủ, nhọt, nang ẩn, dễ để lại sẹo nếu tự ý nặn.",
    image: require("../assets/woundImage/munTC.jpg"),
  },
  {
    id: "vay-nen",
    title: "Vảy nến",
    english: "Psoriasis",
    type: "Miễn dịch - Mãn tính",
    color: "#BE185D", // Đỏ hồng
    desc: "Bệnh lý hệ miễn dịch gây tăng sinh tế bào da quá mức, tạo thành các mảng da dày, đỏ, phủ nhiều vảy trắng bạc. Bệnh không lây nhiễm nhưng dễ tái phát.",
    image: require("../assets/woundImage/vayNen.jpg"),
  },
  {
    id: "nam-da",
    title: "Nấm da",
    english: "Fungal Infections",
    type: "Lây nhiễm vi nấm",
    color: "#0284C7", // Xanh lơ
    desc: "Bệnh viêm nhiễm do nhóm nấm ngoài da Dermatophytes hoặc men nấm gây ra. Dấu hiệu phổ biến là sẩn đỏ, bong tróc viền mụn nước, ranh giới rõ ràng và rất ngứa ngáy.",
    image: require("../assets/woundImage/namDa.jpg"),
  },
];

export default function WoundCategoriesScreen() {
  const insets = useSafeAreaInsets();

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#F8F9FA" />

      {/* ── Top Bar ── */}
      <View style={[styles.header, { paddingTop: insets.top + 10 }]}>
        <TouchableOpacity
          onPress={() => router.back()}
          style={styles.backBtn}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Feather name="arrow-left" size={20} color={Colors.primary} />
        </TouchableOpacity>
        <View style={styles.headerTitleWrap}>
          <Text style={styles.headerTitle}>DANH MỤC VẾT THƯƠNG</Text>
        </View>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView
        contentContainerStyle={{ paddingTop: 16, paddingBottom: insets.bottom + 20 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Lời tựa */}
        <View style={styles.introBlock}>
          {/* <Text style={styles.introTitle}>Từ điển Y tế</Text> */}
          <Text style={styles.introDesc}>
            Tổng hợp thông tin y khoa chi tiết về 6 loại tổn thương và bệnh lý da liễu phổ biến mà SkinAid hỗ trợ nhận diện.
          </Text>
        </View>

        {/* Danh sách thẻ */}
        <View style={styles.listWrap}>
          {WOUND_CATEGORIES.map((cat, index) => (
            <View key={cat.id} style={styles.card}>
              {/* Header card: Màu accent + Hình ảnh Placeholder */}
              <View style={[styles.cardHeader, { backgroundColor: cat.color + "15" }]}>
                {cat.image ? (
                  <Image source={cat.image} style={styles.cardImage} resizeMode="cover" />
                ) : (
                  <View style={styles.cardPlaceholder}>
                    <Feather name="image" size={32} color={cat.color + "50"} />
                    <Text style={[styles.cardPlaceholderText, { color: cat.color + "80" }]}>
                      [ Hình minh họa sẽ cắm vào đây ]
                    </Text>
                  </View>
                )}
                <View style={[styles.badgePill, { backgroundColor: cat.color }]}>
                  <Text style={styles.badgePillText}>{cat.type}</Text>
                </View>
              </View>

              {/* Body card: Tiêu đề + mô tả */}
              <View style={styles.cardBody}>
                <View style={styles.titleRow}>
                  <Text style={styles.cardTitle}>{cat.title}</Text>
                  <Text style={styles.cardSubtitle}>{cat.english}</Text>
                </View>
                <View style={[styles.separator, { backgroundColor: cat.color + "20" }]} />
                <Text style={styles.cardDesc}>{cat.desc}</Text>

                {/* Info action (Hiện đang ẩn theo yêu cầu)
                <TouchableOpacity style={styles.actionBtn}>
                  <Text style={[styles.actionBtnText, { color: cat.color }]}>
                    Xem hướng dẫn sơ cứu
                  </Text>
                  <Feather name="chevron-right" size={16} color={cat.color} />
                </TouchableOpacity> */}
              </View>
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F8F9FA",
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 14,
    backgroundColor: Colors.white,
    // Tạo độ cách biệt với nền
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 3,
    zIndex: 10,
  },
  backBtn: {
    width: 40,
    height: 40,
    alignItems: "center",
    justifyContent: "center",
  },
  headerTitleWrap: {
    flex: 1,
    alignItems: "center",
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: "800",
    color: Colors.primary,
    letterSpacing: 1.5,
  },
  introBlock: {
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 24,
  },
  introTitle: {
    fontSize: 26,
    fontWeight: "800",
    color: Colors.textPrimary,
    marginBottom: 6,
  },
  introDesc: {
    fontSize: 14,
    color: Colors.textLight,
    lineHeight: 22,
  },
  listWrap: {
    paddingHorizontal: 16,
    gap: 20,
  },
  card: {
    backgroundColor: Colors.white,
    borderRadius: 20,
    overflow: "hidden",
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 5,
    borderWidth: 1,
    borderColor: "rgba(0,0,0,0.03)",
  },
  cardHeader: {
    width: "100%",
    height: 180,
    position: "relative",
  },
  cardImage: {
    width: "100%",
    height: "100%",
  },
  cardPlaceholder: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
  },
  cardPlaceholderText: {
    fontSize: 12,
    fontWeight: "600",
  },
  badgePill: {
    position: "absolute",
    top: 14,
    right: 14,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgePillText: {
    fontSize: 10,
    fontWeight: "800",
    color: "#fff",
    letterSpacing: 0.5,
  },
  cardBody: {
    padding: 18,
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: "800",
    color: Colors.textPrimary,
  },
  cardSubtitle: {
    fontSize: 13,
    color: Colors.textMuted,
    fontWeight: "600",
    fontStyle: "italic",
    paddingBottom: 2,
  },
  separator: {
    width: 40,
    height: 3,
    borderRadius: 2,
    marginBottom: 12,
  },
  cardDesc: {
    fontSize: 13.5,
    color: Colors.textLight,
    lineHeight: 22,
  },
  actionBtn: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 16,
    gap: 4,
  },
  actionBtnText: {
    fontSize: 13,
    fontWeight: "700",
  },
});
