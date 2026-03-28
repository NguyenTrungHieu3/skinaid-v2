// app/(tabs)/profile.tsx
import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  Image,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import PersonalInfoEdit from "../../components/profile/PersonalInfoEdit";
import PersonalInfoView, {
  UserInfo,
} from "../../components/profile/PersonalInfoView";
import ProfileHeader from "../../components/profile/ProfileHeader";
import ProfileTabs, { ProfileTab } from "../../components/profile/ProfileTabs";
import SettingsView from "../../components/profile/SettingsView";

const MOCK_USER: UserInfo = {
  fullName: "Thanh Nhàn",
  phone: "",
  birthDate: "",
  gender: "Nữ",
  address: "",
};

const TEAL = "#3DBFA0";
const F = 40;
const C = 10;
const T = 2;

export default function ProfileScreen() {
  const [activeTab, setActiveTab] = useState<ProfileTab>("info");
  const [isEditing, setIsEditing] = useState(false);
  const [userInfo, setUserInfo] = useState<UserInfo>(MOCK_USER);

  const handleSave = (updated: UserInfo) => {
    setUserInfo(updated);
    setIsEditing(false);
  };

  const handleTabChange = (tab: ProfileTab) => {
    setActiveTab(tab);
    setIsEditing(false);
  };

  const handleLogout = () => {
    router.replace("../(tabs)/index");
  };

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />

      {/* App bar */}
      <View style={styles.appBar}>
        <View style={styles.logoRow}>
          <View style={styles.scanFrame}>
            <View style={[styles.corner, styles.cTL]} />
            <View style={[styles.corner, styles.cTR]} />
            <View style={[styles.corner, styles.cBL]} />
            <View style={[styles.corner, styles.cBR]} />
            <Image
              source={require("../../assets/logo_1.png")}
              style={styles.logo}
              resizeMode="contain"
            />
          </View>
          <Text style={styles.appName}>
            <Text style={styles.appLight}>Skin</Text>
            <Text style={styles.appBold}>Aid</Text>
          </Text>
        </View>

        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <Feather name="log-out" size={15} color={TEAL} />
          <Text style={styles.logoutText}>Đăng xuất</Text>
        </TouchableOpacity>
      </View>

      <ScrollView showsVerticalScrollIndicator={false}>
        <ProfileHeader
          name={userInfo.fullName || "Người dùng"}
          memberSince="21/03/2026"
          onPressAvatar={() => console.log("Change avatar")}
        />

        <ProfileTabs activeTab={activeTab} onChangeTab={handleTabChange} />

        {activeTab === "info" ? (
          isEditing ? (
            <PersonalInfoEdit
              info={userInfo}
              onSave={handleSave}
              onCancel={() => setIsEditing(false)}
            />
          ) : (
            <PersonalInfoView
              info={userInfo}
              onPressEdit={() => setIsEditing(true)}
            />
          )
        ) : (
          <SettingsView
            onPressChangePassword={() => router.push("/(auth)/change-password")}
          />
        )}

        <View style={{ height: 32 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#FFFFFF" },
  appBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 12,
    backgroundColor: "#FFFFFF",
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
  },
  logoRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  scanFrame: {
    width: F,
    height: F,
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  corner: { position: "absolute", width: C, height: C, borderColor: TEAL },
  cTL: {
    top: 0,
    left: 0,
    borderTopWidth: T,
    borderLeftWidth: T,
    borderTopLeftRadius: 2,
  },
  cTR: {
    top: 0,
    right: 0,
    borderTopWidth: T,
    borderRightWidth: T,
    borderTopRightRadius: 2,
  },
  cBL: {
    bottom: 0,
    left: 0,
    borderBottomWidth: T,
    borderLeftWidth: T,
    borderBottomLeftRadius: 2,
  },
  cBR: {
    bottom: 0,
    right: 0,
    borderBottomWidth: T,
    borderRightWidth: T,
    borderBottomRightRadius: 2,
  },
  logo: { width: 26, height: 26 },
  appName: { fontSize: 20 },
  appLight: { color: "#1A1A1A", fontWeight: "400" },
  appBold: { color: "#1A1A1A", fontWeight: "700" },
  logoutBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    borderWidth: 1.5,
    borderColor: TEAL,
    borderRadius: 50,
    paddingVertical: 7,
    paddingHorizontal: 14,
  },
  logoutText: {
    fontSize: 13,
    fontWeight: "600",
    color: TEAL,
  },
});
