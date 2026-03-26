import { Feather } from "@expo/vector-icons";
import React, { useState } from "react";
import {
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
} from "react-native";
import {
  AuthHeader,
  BackToLogin,
  InputField,
  PrimaryButton,
  TEAL,
} from "../../components/AuthComponents";

export default function ResetPasswordScreen() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleReset = () => {
    if (password !== confirmPassword) {
      console.log("Passwords do not match");
      return;
    }
    // TODO: xử lý reset password logic
    console.log("Reset password");
  };

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />

      <AuthHeader />

      <Text style={styles.title}>Đặt lại mật khẩu?</Text>

      <Text style={styles.description}>
        Vui lòng nhập mật khẩu mới của bạn bên dưới.
      </Text>

      {/* New Password */}
      <Text style={styles.label}>Mật khẩu mới</Text>
      <InputField
        icon={<Feather name="lock" size={18} color={TEAL} />}
        placeholder="••••••••••"
        value={password}
        onChangeText={setPassword}
        secureTextEntry={!showPassword}
        rightIcon={
          <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
            <Feather
              name={showPassword ? "eye" : "eye-off"}
              size={18}
              color="#B0B8C1"
            />
          </TouchableOpacity>
        }
      />

      {/* Confirm New Password */}
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

      <PrimaryButton label="Đặt lại mật khẩu" onPress={handleReset} />

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
