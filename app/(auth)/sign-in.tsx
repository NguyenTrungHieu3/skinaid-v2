import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import * as SecureStore from "expo-secure-store";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Modal,
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
import { validatePassword, validateUsername } from "../../utils/validation";

export default function SignInScreen() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  const { signIn } = useAuth();
  const [loading, setLoading] = useState(false);
  const [errorModal, setErrorModal] = useState({ visible: false, message: "" });

  const [errors, setErrors] = useState({
    username: "",
    password: "",
  });

  useEffect(() => {
    const loadRemember = async () => {
      const saved = await SecureStore.getItemAsync("rememberMe");
      if (saved !== null) {
        setRememberMe(JSON.parse(saved));
      }
    };
    loadRemember();
  }, []);

  const handleSignIn = async () => {
    if (loading) return;

    const newErrors = {
      username: validateUsername(username),
      password: validatePassword(password),
    };

    setErrors(newErrors);

    if (newErrors.username || newErrors.password) {
      return;
    }

    try {
      setLoading(true);

      await signIn(
        {
          user_name: username,
          password: password,
        },
        rememberMe
      );

      router.replace("/(tabs)/home");
    } catch (error: any) {
      console.error("Login Error:", error);
      setErrorModal({ visible: true, message: getErrorMessage(error) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Error Modal */}
      <Modal
        visible={errorModal.visible}
        transparent
        animationType="fade"
        onRequestClose={() => setErrorModal({ ...errorModal, visible: false })}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            {/* Icon cảnh báo */}
            <View style={styles.modalIconWrap}>
              <Feather name="alert-circle" size={36} color="#EF4444" />
            </View>

            <Text style={styles.modalTitle}>Đăng nhập thất bại</Text>
            <Text style={styles.modalMessage}>Tài khoản hoặc mật khẩu của bạn chưa đúng</Text>

            <TouchableOpacity
              style={styles.modalBtn}
              activeOpacity={0.8}
              onPress={() => setErrorModal({ ...errorModal, visible: false })}
            >
              <Text style={styles.modalBtnText}>OK</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

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
        placeholder="Nhập tên người dùng"
        value={username}
        onChangeText={(text) => {
          setUsername(text);
          if (errors.username) setErrors({ ...errors, username: "" });
        }}
        autoCapitalize="none"
        editable={!loading}
      />

      {errors.username ? (
        <Text style={styles.errorText}>{errors.username}</Text>
      ) : null}

      {/* Password */}
      <Text style={styles.label}>Mật khẩu</Text>
      <InputField
        icon={<Feather name="lock" size={18} color={TEAL} />}
        placeholder="••••••••••"
        value={password}
        onChangeText={(text) => {
          setPassword(text);
          if (errors.password) setErrors({ ...errors, password: "" });
        }}
        secureTextEntry={!showPassword}
        editable={!loading}
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

      {errors.password && (
        <Text style={styles.errorText}>{errors.password}</Text>
      )}

      {/* Remember me + Forgot password */}
      <View style={styles.row}>
        <TouchableOpacity
          style={styles.checkRow}
          onPress={() => !loading && setRememberMe(!rememberMe)}
          disabled={loading}
        >
          <View style={[styles.checkbox, rememberMe && styles.checkboxChecked]}>
            {rememberMe && <Feather name="check" size={11} color="#FFF" />}
          </View>
          <Text style={styles.checkLabel}>Ghi nhớ tôi</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => !loading && router.push("../(auth)/forgot-password")}
          disabled={loading}
        >
          <Text style={styles.forgotText}>Quên mật khẩu?</Text>
        </TouchableOpacity>
      </View>

      {/* Nút đăng nhập với trạng thái Loading */}
      <View style={{ marginTop: 20 }}>
        {loading ? (
          <View style={styles.loadingButton}>
            <ActivityIndicator color="#FFF" size="small" />
            <Text style={styles.loadingText}>Đang đăng nhập...</Text>
          </View>
        ) : (
          <PrimaryButton label="Đăng nhập" onPress={handleSignIn} />
        )}
      </View>

      {/* Register link */}
      <View style={styles.registerRow}>
        <Text style={styles.registerText}>Chưa có tài khoản! </Text>
        <TouchableOpacity
          onPress={() => !loading && router.push("../(auth)/sign-up")}
          disabled={loading}
        >
          <Text style={styles.registerLink}>Đăng kí ngay</Text>
        </TouchableOpacity>
      </View>

      {/* Divider */}
      {/* <View style={styles.dividerRow}>
        <View style={styles.dividerLine} />
        <Text style={styles.dividerText}>Đăng nhập bằng</Text>
        <View style={styles.dividerLine} />
      </View> */}

      {/* Google Button */}
      {/* <TouchableOpacity
        style={[styles.googleBtn, loading && { opacity: 0.5 }]}
        activeOpacity={0.8}
        disabled={loading}
      >
        <Text style={styles.googleIcon}>G</Text>
        <Text style={styles.googleText}>Google</Text>
      </TouchableOpacity> */}
      </ScrollView>
    </>
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
  errorText: {
    color: "#EF4444",
    fontSize: 12,
    marginBottom: 15,
  },
  loadingButton: {
    backgroundColor: TEAL,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 12,
    height: 56,
    gap: 10,
  },
  loadingText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "600",
  },
  // ── Error Modal ──────────────────────────────────────
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.45)",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 32,
  },
  modalCard: {
    width: "100%",
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    paddingVertical: 32,
    paddingHorizontal: 24,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 20,
    elevation: 10,
  },
  modalIconWrap: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: "#FEE2E2",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1A1A1A",
    marginBottom: 10,
    textAlign: "center",
  },
  modalMessage: {
    fontSize: 14,
    color: "#555",
    textAlign: "center",
    lineHeight: 21,
    marginBottom: 24,
  },
  modalBtn: {
    backgroundColor: TEAL,
    borderRadius: 12,
    height: 48,
    width: "100%",
    alignItems: "center",
    justifyContent: "center",
  },
  modalBtnText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
});
