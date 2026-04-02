import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  Alert,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import {
  AuthHeader,
  InputField,
  PrimaryButton,
  TEAL,
} from "../../components/AuthComponents";
import { authService } from "../../services/authService";
import { getErrorMessage } from "../../services/utils";
export default function SignUpScreen() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [email, setEmail] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [agreed, setAgreed] = useState(false);

  const handleSignUp = async () => {
    if (!agreed) return;

    if (password !== confirmPassword) {
      Alert.alert("Lỗi", "Mật khẩu xác nhận không khớp");
      return;
    }

    try {
      // Sửa lại object gửi đi cho đúng với Swagger
      const signUpData = {
        user_name: username, // Phải là user_name (theo Swagger)
        email: email,
        password: password,
        confirm_password: confirmPassword, // Phải có trường này gửi lên server
        gender: "Other", // Swagger yêu cầu phải có gender (bạn có thể thêm input chọn hoặc để mặc định)
      };

      console.log("Data sending:", signUpData); // Log ra để kiểm tra trước khi call

      await authService.signUp(signUpData);

      Alert.alert("Thành công", "Đăng ký tài khoản thành công!", [
        {
          text: "Đăng nhập ngay",
          onPress: () => router.replace("/(auth)/sign-in"),
        },
      ]);
    } catch (error: any) {
      console.log("Error details:", error.response?.data); // Log lỗi chi tiết từ server
      Alert.alert("Lỗi đăng ký", getErrorMessage(error));
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

      <Text style={styles.title}>ĐĂNG KÝ</Text>

      {/* Username */}
      <Text style={styles.label}>Tên người dùng</Text>
      <InputField
        icon={<Feather name="user" size={18} color={TEAL} />}
        placeholder="minhhoang123"
        value={username}
        onChangeText={setUsername}
        autoCapitalize="none"
      />

      {/* Password */}
      <Text style={styles.label}>Mật khẩu</Text>
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

      {/* Confirm Password */}
      <Text style={styles.label}>Xác nhận mật khẩu</Text>
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

      {/* Email */}
      <Text style={styles.label}>Email</Text>
      <InputField
        icon={<Feather name="mail" size={18} color={TEAL} />}
        placeholder="your.email@example.com"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
      />

      {/* Terms checkbox */}
      <TouchableOpacity
        style={styles.termsRow}
        onPress={() => setAgreed(!agreed)}
      >
        <View style={[styles.checkbox, agreed && styles.checkboxChecked]}>
          {agreed && <Feather name="check" size={11} color="#FFF" />}
        </View>
        <Text style={styles.termsText}>
          Tôi đồng ý với <Text style={styles.termsLink}>Điều khoản</Text> và{" "}
          <Text style={styles.termsLink}>Điều kiện</Text>
        </Text>
      </TouchableOpacity>

      <PrimaryButton label="Đăng ký" onPress={handleSignUp} />

      {/* Login link */}
      <View style={styles.loginRow}>
        <Text style={styles.loginText}>Đã có tài khoản! </Text>
        <TouchableOpacity onPress={() => router.replace("../(auth)/sign-in")}>
          <Text style={styles.loginLink}>Đăng nhập</Text>
        </TouchableOpacity>
      </View>
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
    fontSize: 24,
    fontWeight: "700",
    color: TEAL,
    textAlign: "center",
    letterSpacing: 1.5,
    marginBottom: 28,
  },
  label: {
    fontSize: 14,
    fontWeight: "500",
    color: "#1A1A1A",
    marginBottom: 6,
  },
  termsRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 4,
    marginBottom: 4,
  },
  checkbox: {
    width: 16,
    height: 16,
    borderWidth: 1.5,
    borderColor: "#B0B8C1",
    borderRadius: 3,
    alignItems: "center",
    justifyContent: "center",
  },
  checkboxChecked: {
    backgroundColor: TEAL,
    borderColor: TEAL,
  },
  termsText: { fontSize: 13, color: "#555", flex: 1, flexWrap: "wrap" },
  termsLink: { color: TEAL, fontWeight: "500" },
  loginRow: {
    flexDirection: "row",
    justifyContent: "center",
    marginTop: 16,
  },
  loginText: { fontSize: 14, color: "#666" },
  loginLink: { fontSize: 14, color: TEAL, fontWeight: "600" },
});
