import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useState } from "react";
import { Alert, ScrollView, StatusBar, StyleSheet, Text } from "react-native";
import {
  AuthHeader,
  BackToLogin,
  InputField,
  PrimaryButton,
  TEAL,
} from "../../components/AuthComponents";
import { authService } from "../../services/authService";

export default function ForgotPasswordScreen() {
  const [email, setEmail] = useState("");

  const handleSend = async () => {
    try {
      await authService.forgotPassword(email);
      Alert.alert("Thông báo", "Vui lòng kiểm tra email để nhận mã reset");
      router.push("/(auth)/reset-password");
    } catch (error: any) {
      Alert.alert("Lỗi", "Email không tồn tại hoặc lỗi hệ thống");
    }
  };

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />

      <AuthHeader />

      <Text style={styles.title}>Quên mật khẩu?</Text>

      <Text style={styles.description}>
        Đừng lo! Hãy nhập địa chỉ email của bạn và chúng tôi sẽ gửi cho bạn liên
        kết để đặt lại mật khẩu.
      </Text>

      <Text style={styles.label}>Email</Text>
      <InputField
        icon={<Feather name="mail" size={18} color={TEAL} />}
        placeholder="your.email@example.com"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
      />

      <PrimaryButton label="Gửi" onPress={handleSend} />

      <BackToLogin />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 28,
    paddingTop: 64,
    paddingBottom: 40,
  },
  title: {
    fontSize: 26,
    fontWeight: "700",
    color: TEAL,
    textAlign: "center",
    marginBottom: 14,
  },
  description: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: "center",
    lineHeight: 22,
    marginBottom: 28,
    paddingHorizontal: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: "500",
    color: "#1A1A1A",
    marginBottom: 6,
  },
});
