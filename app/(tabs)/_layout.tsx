import { Feather } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import React, { createContext, useContext } from "react";
import { Platform, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Colors } from "../../constants/colors";

const TEAL = Colors.primaryLight;

// ── Chiều cao cố định của phần nội dung tab bar (icon + label) ──
const TAB_CONTENT_HEIGHT = 60;

// ── Context để các screen con lấy được chiều cao tab bar thực tế ──
// Giúp ScrollView/FlatList thêm paddingBottom chính xác, tránh bị tab bar che.
export const TabBarHeightContext = createContext<number>(TAB_CONTENT_HEIGHT);
export const useTabBarHeight = () => useContext(TabBarHeightContext);

export default function TabLayout() {
  const insets = useSafeAreaInsets();

  // ── Tính padding bottom ──
  // iOS: safe area tự xử lý (insets.bottom thường ~34 trên iPhone có notch)
  // Android: insets.bottom = chiều cao system navigation bar (gesture bar / 3-button nav)
  //          Nếu 0 (thiết bị cũ có phím cứng), dùng fallback 12
  const bottomPadding =
    Platform.OS === "ios"
      ? insets.bottom
      : insets.bottom > 0
        ? insets.bottom
        : 12;

  // ── Tổng chiều cao tab bar = nội dung + padding tránh system nav bar ──
  const TAB_BAR_HEIGHT = TAB_CONTENT_HEIGHT + bottomPadding;

  return (
    <TabBarHeightContext.Provider value={TAB_BAR_HEIGHT}>
      <Tabs
        screenOptions={{
          headerShown: false,
          tabBarActiveTintColor: TEAL,
          tabBarInactiveTintColor: "#9CA3AF",
          tabBarShowLabel: true,
          tabBarStyle: {
            backgroundColor: "#FFFFFF",
            borderTopWidth: 1,
            borderTopColor: "#F3F4F6",
            height: TAB_BAR_HEIGHT,
            paddingBottom: bottomPadding,
            paddingTop: 8,
            position: "absolute",
          },
          tabBarLabelStyle: {
            fontSize: 10,
            fontWeight: "500",
          },
        }}
      >
        {/* Tab 1: Home */}
        <Tabs.Screen
          name="home"
          options={{
            title: "Trang chủ",
            tabBarIcon: ({ color }) => (
              <Feather name="home" size={22} color={color} />
            ),
          }}
        />

        {/* Tab 2: Analyst History */}
        <Tabs.Screen
          name="history"
          options={{
            title: "Lịch sử",
            tabBarIcon: ({ color }) => (
              <Feather name="file-text" size={22} color={color} />
            ),
          }}
        />

        {/* Tab 3: Scan — nút tròn nổi ở giữa */}
        <Tabs.Screen
          name="scan"
          options={{
            title: "",
            tabBarStyle: { display: "none" },
            tabBarIcon: ({ focused }) => (
              <View
                style={[
                  styles.scanBtn,
                  focused && styles.scanBtnFocused,
                  {
                    marginBottom: bottomPadding + 5,
                  },
                ]}
              >
                <Feather name="camera" size={26} color="#FFFFFF" />
              </View>
            ),
            tabBarLabel: () => null,
          }}
        />

        {/* Tab 4: Medical Facilities */}
        <Tabs.Screen
          name="facilities"
          options={{
            title: "Cơ sở y tế",
            tabBarIcon: ({ color }) => (
              <Feather name="map-pin" size={22} color={color} />
            ),
          }}
        />

        {/* Tab 5: Profile */}
        <Tabs.Screen
          name="profile"
          options={{
            title: "Hồ sơ cá nhân",
            tabBarIcon: ({ color }) => (
              <Feather name="user" size={22} color={color} />
            ),
          }}
        />
      </Tabs>
    </TabBarHeightContext.Provider>
  );
}

const styles = StyleSheet.create({
  scanBtn: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: TEAL,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: TEAL,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.45,
    shadowRadius: 10,
    elevation: 8,
  },
  scanBtnFocused: {
    backgroundColor: "#2EA88A",
  },
});
