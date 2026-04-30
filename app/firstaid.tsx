import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  FlatList,
  Image,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  Dimensions,
  Modal,
  Pressable,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Colors } from "../constants/colors";

const { width, height } = Dimensions.get("window");

const FIRST_AID_TOOLS = [
  {
    id: "saline",
    title: "Nước muối sinh lý",
    usage: "Rửa sạch vết thương, loại bỏ dị vật và vi khuẩn mà không gây xót.",
    where: "Hiệu thuốc (Dạng chai 500ml hoặc ống nhỏ).",
    image: require("../assets/medicalTool/nuocMuoi.jpg"),
    color: "#3B82F6",
  },
  {
    id: "povidine",
    title: "Dung dịch Povidine",
    usage: "Sát khuẩn vùng da xung quanh vết thương để ngăn ngừa nhiễm trùng.",
    where: "Hiệu thuốc (Chai màu nâu đỏ).",
    image: require("../assets/medicalTool/povidine.png"),
    color: "#B91C1C",
  },
  {
    id: "gauze",
    title: "Gạc vô trùng",
    usage: "Thấm dịch và bảo vệ vết thương khỏi bụi bẩn và va chạm bên ngoài.",
    where: "Hiệu thuốc, siêu thị.",
    image: require("../assets/medicalTool/gacVoTrung.jpg"),
    color: "#9CA3AF",
  },
  {
    id: "bandage",
    title: "Băng cá nhân (Urgo)",
    usage: "Che phủ các vết trầy xước hoặc vết cắt nhỏ để cầm máu và bảo vệ.",
    where: "Cửa hàng tiện lợi, hiệu thuốc.",
    image: require("../assets/medicalTool/bangCaNhan.jpg"),
    color: "#F59E0B",
  },
  {
    id: "scissors",
    title: "Kéo y tế",
    usage: "Dùng để cắt băng gạc, vải quấn hoặc quần áo trong trường hợp khẩn cấp.",
    where: "Cửa hàng thiết bị y tế.",
    image: require("../assets/medicalTool/keoYTe.jpg"),
    color: "#374151",
  },
];

const WOUND_FIRST_AID = [
  {
    id: "tray-xuoc",
    title: "Trầy xước",
    image: require("../assets/woundImage/trayXuoc.jpg"),
    steps: [
      "Rửa sạch vết thương dưới vòi nước sạch hoặc nước muối sinh lý.",
      "Dùng gạc thấm khô và bôi thuốc mỡ kháng sinh (nếu cần).",
      "Băng nhẹ bằng băng cá nhân hoặc gạc mỏng.",
    ],
    color: "#E25A3B",
  },
  {
    id: "bam-tim",
    title: "Bầm tím",
    image: require("../assets/woundImage/bam.jpg"),
    steps: [
      "Chườm đá lạnh trong 24 giờ đầu (15-20 phút mỗi lần) để giảm sưng.",
      "Sau 48 giờ, có thể chườm ấm để tăng cường lưu thông máu.",
      "Hạn chế vận động mạnh vùng bị bầm.",
    ],
    color: "#5C4B99",
  },
  {
    id: "bong",
    title: "Bỏng",
    image: require("../assets/woundImage/bong.jpg"),
    steps: [
      "Xả vùng bị bỏng dưới vòi nước mát trong 15-20 phút (không dùng đá).",
      "Dùng gạc vô trùng che nhẹ vết bỏng, không băng quá chặt.",
      "Tuyệt đối không bôi kem đánh răng hoặc mỡ trăn.",
    ],
    color: "#D97706",
  },
  {
    id: "mun-trung-ca",
    title: "Mụn trứng cá",
    image: require("../assets/woundImage/munTC.jpg"),
    steps: [
      "Rửa mặt bằng sữa rửa mặt dịu nhẹ 2 lần/ngày.",
      "Không tự ý nặn mụn để tránh viêm nhiễm và để lại sẹo.",
      "Sử dụng các loại thuốc chấm mụn chứa Benzoyl Peroxide hoặc Salicylic Acid.",
    ],
    color: "#059669",
  },
  {
    id: "vay-nen",
    title: "Vảy nến",
    image: require("../assets/woundImage/vayNen.jpg"),
    steps: [
      "Dưỡng ẩm da thường xuyên bằng kem chuyên dụng.",
      "Hạn chế gãi và tránh các yếu tố kích thích (stress, rượu bia).",
      "Tuân thủ phác đồ điều trị của bác sĩ chuyên khoa.",
    ],
    color: "#BE185D",
  },
  {
    id: "nam-da",
    title: "Nấm da",
    image: require("../assets/woundImage/namDa.jpg"),
    steps: [
      "Giữ vùng da bị nấm luôn khô ráo và thoáng mát.",
      "Bôi kem kháng nấm đều đặn theo hướng dẫn.",
      "Không dùng chung vật dụng cá nhân (khăn, lược, quần áo).",
    ],
    color: "#0284C7",
  },
];

export default function FirstAidScreen() {
  const insets = useSafeAreaInsets();
  const [activeTab, setActiveTab] = useState<"tools" | "wounds">("tools");
  const [zoomImage, setZoomImage] = useState<any>(null);

  const renderToolItem = ({ item }: { item: typeof FIRST_AID_TOOLS[0] }) => (
    <View style={styles.toolCard}>
      <TouchableOpacity 
        style={styles.toolIconBox} 
        activeOpacity={0.8}
        onPress={() => setZoomImage(item.image)}
      >
        <Image source={item.image} style={styles.toolImageThumb} resizeMode="cover" />
      </TouchableOpacity>
      <View style={styles.toolContent}>
        <Text style={styles.toolTitle}>{item.title}</Text>
        <Text style={styles.toolUsage}>{item.usage}</Text>
        <View style={styles.whereToBuy}>
          <Feather name="shopping-cart" size={12} color={Colors.textLight} />
          <Text style={styles.whereText}>{item.where}</Text>
        </View>
      </View>
    </View>
  );

  const renderWoundItem = ({ item }: { item: typeof WOUND_FIRST_AID[0] }) => (
    <View style={styles.woundCard}>
      <TouchableOpacity 
        activeOpacity={0.9} 
        onPress={() => setZoomImage(item.image)}
      >
        <Image source={item.image} style={styles.woundImage} resizeMode="cover" />
      </TouchableOpacity>
      <View style={styles.woundContent}>
        <Text style={[styles.woundTitle, { color: item.color }]}>{item.title}</Text>
        {item.steps.map((step, idx) => (
          <View key={idx} style={styles.stepRow}>
            <View style={[styles.stepDot, { backgroundColor: item.color }]} />
            <Text style={styles.stepText}>{step}</Text>
          </View>
        ))}
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent />
      
      <LinearGradient colors={Colors.gradientHero} style={[styles.header, { paddingTop: insets.top + 20 }]}>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Feather name="arrow-left" size={24} color={Colors.white} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>CẨM NANG SƠ CỨU</Text>
        <View style={{ width: 40 }} />
      </LinearGradient>

      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, activeTab === "tools" && styles.activeTab]}
          onPress={() => setActiveTab("tools")}
        >
          <Text style={[styles.tabText, activeTab === "tools" && styles.activeTabText]}>Dụng cụ</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === "wounds" && styles.activeTab]}
          onPress={() => setActiveTab("wounds")}
        >
          <Text style={[styles.tabText, activeTab === "wounds" && styles.activeTabText]}>Vết thương</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={activeTab === "tools" ? FIRST_AID_TOOLS : WOUND_FIRST_AID}
        keyExtractor={(item) => item.id}
        renderItem={activeTab === "tools" ? renderToolItem : renderWoundItem}
        contentContainerStyle={[
          styles.listContainer,
          { paddingBottom: insets.bottom + 20 }
        ]}
        showsVerticalScrollIndicator={false}
      />

      {/* ── Zoom Modal ── */}
      <Modal
        visible={!!zoomImage}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setZoomImage(null)}
      >
        <Pressable 
          style={styles.modalOverlay}
          onPress={() => setZoomImage(null)}
        >
          <View style={styles.zoomContainer}>
            {zoomImage && (
              <Image 
                source={zoomImage} 
                style={styles.fullImage} 
                resizeMode="contain" 
              />
            )}
            <TouchableOpacity 
              style={styles.closeZoomBtn}
              onPress={() => setZoomImage(null)}
            >
              <Feather name="x" size={28} color={Colors.white} />
            </TouchableOpacity>
          </View>
        </Pressable>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.backgroundSecondary,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    paddingBottom: 25,
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
  },
  backBtn: {
    width: 40,
    height: 40,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.2)",
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: Colors.white,
    letterSpacing: 1,
  },
  tabBar: {
    flexDirection: "row",
    marginHorizontal: 20,
    marginTop: -20,
    backgroundColor: Colors.white,
    borderRadius: 15,
    padding: 5,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: "center",
    borderRadius: 12,
  },
  activeTab: {
    backgroundColor: Colors.primary,
  },
  tabText: {
    fontSize: 14,
    fontWeight: "700",
    color: Colors.textMuted,
  },
  activeTabText: {
    color: Colors.white,
  },
  listContainer: {
    paddingTop: 20,
    paddingHorizontal: 20,
  },
  // Tool Card
  toolCard: {
    flexDirection: "row",
    backgroundColor: Colors.white,
    borderRadius: 20,
    padding: 15,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "rgba(0,0,0,0.03)",
    alignItems: "center",
  },
  toolIconBox: {
    width: 70,
    height: 70,
    borderRadius: 15,
    overflow: "hidden",
    backgroundColor: "#F3F4F6",
  },
  toolImageThumb: {
    width: "100%",
    height: "100%",
  },
  toolContent: {
    flex: 1,
    marginLeft: 15,
  },
  toolTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.textPrimary,
    marginBottom: 4,
  },
  toolUsage: {
    fontSize: 13,
    color: Colors.textLight,
    lineHeight: 18,
    marginBottom: 8,
  },
  whereToBuy: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  whereText: {
    fontSize: 12,
    color: Colors.textMuted,
    fontStyle: "italic",
  },
  // Wound Card
  woundCard: {
    backgroundColor: Colors.white,
    borderRadius: 25,
    overflow: "hidden",
    marginBottom: 20,
    borderWidth: 1,
    borderColor: "rgba(0,0,0,0.03)",
  },
  woundImage: {
    width: "100%",
    height: 180,
  },
  woundContent: {
    padding: 20,
  },
  woundTitle: {
    fontSize: 20,
    fontWeight: "800",
    marginBottom: 15,
  },
  stepRow: {
    flexDirection: "row",
    marginBottom: 10,
    paddingRight: 10,
  },
  stepDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginTop: 6,
    marginRight: 12,
  },
  stepText: {
    flex: 1,
    fontSize: 14,
    color: Colors.textDark,
    lineHeight: 20,
  },
  // Modal Zoom
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.9)",
    justifyContent: "center",
    alignItems: "center",
  },
  zoomContainer: {
    width: width,
    height: height,
    justifyContent: "center",
    alignItems: "center",
  },
  fullImage: {
    width: width,
    height: height * 0.8,
  },
  closeZoomBtn: {
    position: "absolute",
    top: 50,
    right: 25,
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "rgba(255,255,255,0.2)",
    justifyContent: "center",
    alignItems: "center",
  },
});
