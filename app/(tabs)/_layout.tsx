// app/(tabs)/_layout.tsx
import { Feather } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import { StyleSheet, View } from "react-native";

const TEAL = "#3DBFA0";

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: TEAL,
        tabBarInactiveTintColor: "#9CA3AF",
        tabBarStyle: {
          backgroundColor: "#FFFFFF",
          borderTopWidth: 1,
          borderTopColor: "#F3F4F6",
          height: 68,
          paddingBottom: 10,
          paddingTop: 8,
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
          title: "Home",
          tabBarIcon: ({ color }) => (
            <Feather name="home" size={22} color={color} />
          ),
        }}
      />

      {/* Tab 2: Analyst History */}
      <Tabs.Screen
        name="history"
        options={{
          title: "Analyst History",
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
            <View style={[styles.scanBtn, focused && styles.scanBtnFocused]}>
              <Feather name="camera" size={26} color="#FFFFFF" />
            </View>
          ),
          tabBarLabel: () => null, // ẩn label
        }}
      />

      {/* Tab 4: Medical Facilities */}
      <Tabs.Screen
        name="facilities"
        options={{
          title: "Medical Facilities",
          tabBarIcon: ({ color }) => (
            <Feather name="map-pin" size={22} color={color} />
          ),
        }}
      />

      {/* Tab 5: Profile */}
      <Tabs.Screen
        name="profile"
        options={{
          title: "Profile",
          tabBarIcon: ({ color }) => (
            <Feather name="user" size={22} color={color} />
          ),
        }}
      />

      {/* Ẩn Welcome screen khỏi tab bar */}
      <Tabs.Screen name="index" options={{ href: null }} />
    </Tabs>
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
    // Nhích lên trên tab bar
    marginBottom: 24,
    // Shadow
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
