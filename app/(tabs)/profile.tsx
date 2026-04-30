// app/(tabs)/profile.tsx
import { Feather } from "@expo/vector-icons";
import * as ImagePicker from "expo-image-picker";
import { router } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Image,
  Keyboard,
  Platform,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useAuth } from "../../context/AuthContext";
import { useTabBarHeight } from "./_layout";

import PersonalInfoEdit from "../../components/profile/PersonalInfoEdit";
import PersonalInfoView, {
  UserInfo,
} from "../../components/profile/PersonalInfoView";
import ProfileHeader from "../../components/profile/ProfileHeader";
import ProfileTabs, { ProfileTab } from "../../components/profile/ProfileTabs";
import SettingsView from "../../components/profile/SettingsView";
import { Colors } from "../../constants/colors";
import { authService } from "../../services/authService";

const EMPTY_USER: UserInfo = {
  fullName: "",
  phone: "",
  birthDate: "",
  gender: "",
  address: "",
};

export default function ProfileScreen() {
  const [activeTab, setActiveTab] = useState<ProfileTab>("info");
  const [isEditing, setIsEditing] = useState(false);
  const [userInfo, setUserInfo] = useState<UserInfo>(EMPTY_USER);
  const [avatarUrl, setAvatarUrl] = useState<string | undefined>(undefined);
  const [memberSince, setMemberSince] = useState<string>("");
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);

  const { signOut, token } = useAuth();
  const tabBarHeight = useTabBarHeight();
  const [keyboardHeight, setKeyboardHeight] = useState(0);

  // Track keyboard height for bottom padding
  useEffect(() => {
    const showEvent = Platform.OS === "ios" ? "keyboardWillShow" : "keyboardDidShow";
    const hideEvent = Platform.OS === "ios" ? "keyboardWillHide" : "keyboardDidHide";
    const showSub = Keyboard.addListener(showEvent, (e) =>
      setKeyboardHeight(e.endCoordinates.height)
    );
    const hideSub = Keyboard.addListener(hideEvent, () =>
      setKeyboardHeight(0)
    );
    return () => { showSub.remove(); hideSub.remove(); };
  }, []);

  // Fetch profile từ API khi vào màn hình
  useEffect(() => {
    fetchProfile();
  }, [token]);

  const fetchProfile = async () => {
    try {
      setIsLoadingProfile(true);
      const res = await authService.getProfile();
      const data = res.data?.data || res.data;

      if (data) {
        setUserInfo({
          fullName: data.full_name || "",
          phone: data.phone || "",
          birthDate: data.date_of_birth
            ? (() => {
                const bd = new Date(data.date_of_birth);
                const dd = String(bd.getDate()).padStart(2, "0");
                const mm = String(bd.getMonth() + 1).padStart(2, "0");
                return `${dd}/${mm}/${bd.getFullYear()}`;
              })()
            : "",
          gender: data.gender_display || data.gender || "",
          address: data.address || "",
        });
        // Cache-busting: ảnh đại diện thường hay bị React Native cache lại dù đã đổi file
        setAvatarUrl(data.avatar_url ? `${data.avatar_url}?t=${Date.now()}` : undefined);

        // Định dạng ngày tạo tài khoản
        if (data.created_at) {
          const d = new Date(data.created_at);
          setMemberSince(d.toLocaleDateString("vi-VN"));
        }
      }
    } catch {
      // Giữ nguyên state trống nếu lỗi
    } finally {
      setIsLoadingProfile(false);
    }
  };

  const handleSave = (updated: UserInfo) => {
    setUserInfo(updated);
    setIsEditing(false);
    // Refetch để có dữ liệu mới nhất từ server
    fetchProfile();
  };

  const handleAvatarPress = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") {
      Alert.alert("Quyền truy cập", "Cần quyền truy cập thư viện ảnh để đổi avatar.");
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });

    if (result.canceled || !result.assets?.[0]) return;

    const asset = result.assets[0];
    const formData = new FormData();
    formData.append("file", {
      uri: asset.uri,
      name: asset.fileName || `avatar_${Date.now()}.jpg`,
      type: asset.mimeType || "image/jpeg",
    } as unknown as Blob);

    try {
      const res = await authService.uploadAvatar(formData);
      const data = res.data?.data || res.data;
      if (data?.avatar_url) {
        // Cache-busting ngay sau khi upload để UI render hình nền mới
        setAvatarUrl(`${data.avatar_url}?t=${Date.now()}`);
        Alert.alert("Thành công", "Cập nhật ảnh đại diện thành công!");
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { message?: string } } };
      const msg = err?.response?.data?.message || "Upload ảnh thất bại. Vui lòng thử lại.";
      Alert.alert("Lỗi", msg);
    }
  };

  const handleTabChange = (tab: ProfileTab) => {
    setActiveTab(tab);
    setIsEditing(false);
  };

  const handleLogout = async () => {
    try {
      await signOut();
      router.replace("/(auth)/sign-in");
    } catch {
      router.replace("/(auth)/sign-in");
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" backgroundColor={Colors.background} />

      {/* App bar */}
      <View style={styles.appBar}>
        <View style={styles.logoRow}>
          <View style={styles.scanFrame}>
            <Image
              source={require("../../assets/logo_1.png")}
              style={styles.logo}
              resizeMode="contain"
            />
          </View>
          <Text style={styles.appName}>Skin<Text style={styles.appNameAccent}>Aid</Text></Text>
        </View>

        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <Feather name="log-out" size={15} color={Colors.primary} />
          <Text style={styles.logoutText}>Đăng xuất</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {isLoadingProfile ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={Colors.primary} />
          </View>
        ) : (
          <>
            <ProfileHeader
              name={userInfo.fullName || "Người dùng"}
              memberSince={memberSince}
              avatarUri={avatarUrl}
              onPressAvatar={handleAvatarPress}
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
          </>
        )}

        <View style={{ height: Math.max(tabBarHeight + 10, keyboardHeight) }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const F = 40;

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  loadingContainer: {
    flex: 1,
    minHeight: 300,
    alignItems: "center",
    justifyContent: "center",
  },
  appBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    paddingTop: 18,
    paddingBottom: 12,
    backgroundColor: Colors.background,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  logoRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  scanFrame: {
    width: F,
    height: F,
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  logo: { width: 36, height: 36 },
  appName: {
    fontSize: 20,
    fontWeight: "700",
    color: "#1A1A1A",
    letterSpacing: 0.3,
  },
  appNameAccent: {
    color: "#02A18D",
  },
  logoutBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    borderWidth: 1.5,
    borderColor: Colors.primary,
    borderRadius: 50,
    paddingVertical: 7,
    paddingHorizontal: 14,
  },
  logoutText: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.primary,
  },
});
