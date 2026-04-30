// app/(auth)/change-password.tsx
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
import { SafeAreaView } from "react-native-safe-area-context";
import { InputField, PrimaryButton } from "../../components/AuthComponents";
import { authService } from "../../services/authService";
import {
  validateConfirmPassword,
  validateOldVsNewPassword,
  validatePassword,
} from "../../utils/validation";

const TEAL = "#3DBFA0";

export default function ChangePasswordScreen() {
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const [errors, setErrors] = useState({
    oldPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  const validate = (): boolean => {
    const errs = {
      oldPassword: "",
      newPassword: "",
      confirmPassword: "",
    };

    if (!oldPassword) errs.oldPassword = "Mật khẩu cũ không được để trống";

    const newPassErr = validatePassword(newPassword);
    if (newPassErr) errs.newPassword = newPassErr;

    const sameErr = validateOldVsNewPassword(oldPassword, newPassword);
    if (sameErr) errs.newPassword = sameErr;

    const confirmErr = validateConfirmPassword(newPassword, confirmPassword);
    if (confirmErr) errs.confirmPassword = confirmErr;

    setErrors(errs);
    return !errs.oldPassword && !errs.newPassword && !errs.confirmPassword;
  };

  const handleChange = async () => {
    if (!validate()) return;

    try {
      setIsLoading(true);
      await authService.changePassword({
        old_password: oldPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });

      Alert.alert("Thành công", "Mật khẩu đã được đổi thành công!", [
        { text: "OK", onPress: () => router.back() },
      ]);
    } catch (e: any) {
      const status = e?.response?.status;
      const msg = e?.response?.data?.message;

      if (status === 400 || status === 401) {
        // Mật khẩu cũ sai
        setErrors((prev) => ({
          ...prev,
          oldPassword: msg || "Mật khẩu cũ không đúng",
        }));
      } else {
        Alert.alert("Lỗi", msg || "Đổi mật khẩu thất bại. Vui lòng thử lại.");
      }
    } finally {
      setIsLoading(false);
    }
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

        <Text style={styles.title}>Đổi mật khẩu</Text>
        <Text style={styles.description}>
          Mật khẩu mới phải có ít nhất 8 ký tự, bao gồm chữ hoa, số và ký tự
          đặc biệt.
        </Text>

        {/* Old password */}
        <Text style={styles.label}>Mật khẩu cũ</Text>
        <InputField
          icon={<Feather name="lock" size={18} color={TEAL} />}
          placeholder="••••••••••"
          value={oldPassword}
          onChangeText={(v) => {
            setOldPassword(v);
            setErrors((p) => ({ ...p, oldPassword: "" }));
          }}
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
        {!!errors.oldPassword && (
          <Text style={styles.errorText}>{errors.oldPassword}</Text>
        )}

        {/* New password */}
        <Text style={[styles.label, { marginTop: 12 }]}>Mật khẩu mới</Text>
        <InputField
          icon={<Feather name="lock" size={18} color={TEAL} />}
          placeholder="••••••••••"
          value={newPassword}
          onChangeText={(v) => {
            setNewPassword(v);
            setErrors((p) => ({ ...p, newPassword: "" }));
          }}
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
        {!!errors.newPassword && (
          <Text style={styles.errorText}>{errors.newPassword}</Text>
        )}

        {/* Confirm new password */}
        <Text style={[styles.label, { marginTop: 12 }]}>
          Xác nhận mật khẩu mới
        </Text>
        <InputField
          icon={<Feather name="lock" size={18} color={TEAL} />}
          placeholder="••••••••••"
          value={confirmPassword}
          onChangeText={(v) => {
            setConfirmPassword(v);
            setErrors((p) => ({ ...p, confirmPassword: "" }));
          }}
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
        {!!errors.confirmPassword && (
          <Text style={styles.errorText}>{errors.confirmPassword}</Text>
        )}

        <View style={{ marginTop: 24 }}>
          <PrimaryButton
            label={isLoading ? "Đang xử lý..." : "Đổi mật khẩu"}
            onPress={handleChange}
            disabled={isLoading}
          />
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
  errorText: {
    fontSize: 12,
    color: "#EF4444",
    marginTop: 4,
    marginBottom: 4,
  },
});
