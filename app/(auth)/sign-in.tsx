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
import { useAuth } from "../../context/AuthContext";
import { getErrorMessage } from "../../services/utils";

export default function SignInScreen() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const { signIn } = useAuth();
  const [loading, setLoading] = useState(false);

  // Trong file sign-in.tsx
  const handleSignIn = async () => {
    if (!username || !password) {
      Alert.alert("Lỗi", "Vui lòng nhập đầy đủ thông tin");
      return;
    }

    try {
      setLoading(true);
      // Gửi đúng key "user_name" như Swagger yêu cầu
      await signIn({
        user_name: username,
        password: password,
      });
      router.replace("/(tabs)/home");
    } catch (error: any) {
      Alert.alert("Đăng nhập thất bại", getErrorMessage(error));
    } finally {
      setLoading(false);
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

      <Text style={styles.title}>ĐĂNG NHẬP</Text>

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

      {/* Remember me + Forgot password */}
      <View style={styles.row}>
        <TouchableOpacity
          style={styles.checkRow}
          onPress={() => setRememberMe(!rememberMe)}
        >
          <View style={[styles.checkbox, rememberMe && styles.checkboxChecked]}>
            {rememberMe && <Feather name="check" size={11} color="#FFF" />}
          </View>
          <Text style={styles.checkLabel}>Ghi nhớ tôi</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => router.push("../(auth)/forgot-password")}
        >
          <Text style={styles.forgotText}>Quên mật khẩu?</Text>
        </TouchableOpacity>
      </View>

      <PrimaryButton label="Đăng nhập" onPress={handleSignIn} />

      {/* Register link */}
      <View style={styles.registerRow}>
        <Text style={styles.registerText}>Chưa có tài khoản! </Text>
        <TouchableOpacity onPress={() => router.push("../(tabs)/home")}>
          <Text style={styles.registerLink}>Đăng kí ngay</Text>
        </TouchableOpacity>
      </View>

      {/* Divider */}
      <View style={styles.dividerRow}>
        <View style={styles.dividerLine} />
        <Text style={styles.dividerText}>Đăng nhập bằng</Text>
        <View style={styles.dividerLine} />
      </View>

      {/* Google Button */}
      <TouchableOpacity style={styles.googleBtn} activeOpacity={0.8}>
        <Text style={styles.googleIcon}>G</Text>
        <Text style={styles.googleText}>Google</Text>
      </TouchableOpacity>
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
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  checkRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
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
  checkLabel: {
    fontSize: 13,
    color: "#555",
  },
  forgotText: {
    fontSize: 13,
    color: TEAL,
    fontWeight: "500",
  },
  registerRow: {
    flexDirection: "row",
    justifyContent: "center",
    marginTop: 16,
  },
  registerText: { fontSize: 14, color: "#666" },
  registerLink: { fontSize: 14, color: TEAL, fontWeight: "600" },
  dividerRow: {
    flexDirection: "row",
    alignItems: "center",
    marginVertical: 20,
    gap: 10,
  },
  dividerLine: { flex: 1, height: 1, backgroundColor: "#E5E7EB" },
  dividerText: { fontSize: 12, color: "#9CA3AF" },
  googleBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1.5,
    borderColor: "#E5E7EB",
    borderRadius: 50,
    height: 52,
    gap: 10,
  },
  googleIcon: {
    fontSize: 18,
    fontWeight: "700",
    color: "#4285F4",
  },
  googleText: {
    fontSize: 16,
    fontWeight: "500",
    color: "#1A1A1A",
  },
});
