// app/(auth)/change-password.tsx
import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { InputField, PrimaryButton } from "../../components/AuthComponents";

const TEAL = "#3DBFA0";

export default function ChangePasswordScreen() {
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleChange = () => {
    if (newPassword !== confirmPassword) {
      console.log("Mật khẩu xác nhận không khớp");
      return;
    }
    // TODO: gọi API đổi mật khẩu
    console.log("Change password");
    router.back();
  };

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />

      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* Back button */}
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Feather name="arrow-left" size={22} color="#1A1A1A" />
        </TouchableOpacity>

        <Text style={styles.title}>Đổi mật khẩu?</Text>
        <Text style={styles.description}>
          Vui lòng nhập mật khẩu mới của bạn bên dưới.
        </Text>

        {/* Old password */}
        <Text style={styles.label}>Mật khẩu cũ</Text>
        <InputField
          icon={<Feather name="lock" size={18} color={TEAL} />}
          placeholder="••••••••••"
          value={oldPassword}
          onChangeText={setOldPassword}
          secureTextEntry={!showOld}
          rightIcon={
            <TouchableOpacity onPress={() => setShowOld(!showOld)}>
              <Feather
                name={showOld ? "eye" : "eye-off"}
                size={18}
                color="#B0B8C1"
              />
            </TouchableOpacity>
          }
        />

        {/* New password */}
        <Text style={styles.label}>Mật khẩu mới</Text>
        <InputField
          icon={<Feather name="lock" size={18} color={TEAL} />}
          placeholder="••••••••••"
          value={newPassword}
          onChangeText={setNewPassword}
          secureTextEntry={!showNew}
          rightIcon={
            <TouchableOpacity onPress={() => setShowNew(!showNew)}>
              <Feather
                name={showNew ? "eye" : "eye-off"}
                size={18}
                color="#B0B8C1"
              />
            </TouchableOpacity>
          }
        />

        {/* Confirm new password */}
        <Text style={styles.label}>Xác nhận mật khẩu mới</Text>
        <InputField
          icon={<Feather name="lock" size={18} color={TEAL} />}
          placeholder="••••••••••"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          secureTextEntry={!showConfirm}
          rightIcon={
            <TouchableOpacity onPress={() => setShowConfirm(!showConfirm)}>
              <Feather
                name={showConfirm ? "eye" : "eye-off"}
                size={18}
                color="#B0B8C1"
              />
            </TouchableOpacity>
          }
        />

        <View style={{ marginTop: 8 }}>
          <PrimaryButton label="Đổi mật khẩu" onPress={handleChange} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#FFFFFF" },
  container: {
    flexGrow: 1,
    paddingHorizontal: 28,
    paddingTop: 56,
    paddingBottom: 40,
  },
  backBtn: {
    marginBottom: 24,
    alignSelf: "flex-start",
  },
  title: {
    fontSize: 26,
    fontWeight: "700",
    color: "#1A1A1A",
    marginBottom: 10,
  },
  description: {
    fontSize: 14,
    color: "#6B7280",
    lineHeight: 22,
    marginBottom: 28,
  },
  label: {
    fontSize: 14,
    fontWeight: "500",
    color: "#1A1A1A",
    marginBottom: 6,
  },
});
