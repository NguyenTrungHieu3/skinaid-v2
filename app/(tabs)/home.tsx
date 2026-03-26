// app/(tabs)/home.tsx
import { router } from "expo-router";
import React, { useCallback } from "react";
import {
  FlatList,
  SafeAreaView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";

import HeroSection from "../../components/home/HeroSection";
import HomeHeader from "../../components/home/HomeHeader";
import StatsBar from "../../components/home/StatsBar";
import WoundTypeCard from "../../components/home/WoundTypeCard";
import { WOUND_TYPES, WoundType } from "../../constants/woundTypes";

export default function HomeScreen() {
  const handleScan = () => {
    router.push("./(tabs)/scan");
  };

  const handleWoundTypePress = useCallback((item: WoundType) => {
    // TODO: navigate to wound detail/scan with type pre-selected
    console.log("Selected wound type:", item.id);
  }, []);

  // Render card theo dạng 2 cột
  const renderCard = ({ item }: { item: WoundType }) => (
    <WoundTypeCard item={item} onPress={handleWoundTypePress} />
  );

  const renderHeader = () => (
    <View style={styles.content}>
      <HeroSection onPressScan={handleScan} />

      <Text style={styles.sectionTitle}>
        Các loại vết thương có thể nhận diện
      </Text>
    </View>
  );

  const renderFooter = () => (
    <View style={styles.footerPad}>
      <StatsBar />
    </View>
  );

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />

      {/* Header cố định phía trên */}
      <HomeHeader
        onPressNotification={() => console.log("Notifications")}
        onPressProfile={() => router.push("./(tabs)/profile")}
      />

      {/* Danh sách cuộn */}
      <FlatList
        data={WOUND_TYPES}
        keyExtractor={(item) => item.id}
        renderItem={renderCard}
        numColumns={2}
        ListHeaderComponent={renderHeader}
        ListFooterComponent={renderFooter}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        columnWrapperStyle={styles.row}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: "#FFFFFF",
  },
  content: {
    paddingHorizontal: 20,
    paddingTop: 4,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1A1A1A",
    marginBottom: 4,
  },
  listContent: {
    paddingHorizontal: 15,
    paddingBottom: 20,
  },
  row: {
    justifyContent: "space-between",
  },
  footerPad: {
    paddingHorizontal: 5,
    paddingTop: 8,
  },
});
