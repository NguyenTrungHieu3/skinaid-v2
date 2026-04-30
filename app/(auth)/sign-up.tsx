import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  Alert,
  Keyboard,
  Platform,
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
import {
  validateConfirmPassword,
  validateEmail,
  validatePassword,
  validateUsername,
} from "../../utils/validation";

export default function SignUpScreen() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [gender, setGender] = useState<"Male" | "Female">("Male");
  const [email, setEmail] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const [errors, setErrors] = useState({
    username: "",
    password: "",
    confirmPassword: "",
    email: "",
  });
  const isValid =
    !errors.username &&
    !errors.password &&
    !errors.confirmPassword &&
    !errors.email &&
    username &&
    password &&
    confirmPassword &&
    email &&
    agreed;

  const [showAlert, setShowAlert] = useState(false);
  const [alertMessage, setAlertMessage] = useState("");
  const [keyboardHeight, setKeyboardHeight] = useState(0);

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

  const handleSignUp = async () => {
    const newErrors = {
      username: validateUsername(username),
      password: validatePassword(password),
      confirmPassword: validateConfirmPassword(password, confirmPassword),
      email: validateEmail(email),
    };

    setErrors(newErrors);

    // Nếu có lỗi thì dừng
    if (
      newErrors.username ||
      newErrors.password ||
      newErrors.confirmPassword ||
      newErrors.email
    ) {
      return;
    }

    if (!agreed) {
      setAlertMessage("Bạn chưa đồng ý điều khoản");
      setShowAlert(true);
      return;
    }

    try {
      // Sửa lại object gửi đi cho đúng với Swagger
      const signUpData = {
        user_name: username, // Phải là user_name (theo Swagger)
        email: email,
        password: password,
        confirm_password: confirmPassword, // Phải có trường này gửi lên server
        gender: gender, // dùng state mới
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
      contentContainerStyle={[styles.container, keyboardHeight > 0 && { paddingBottom: keyboardHeight }]}
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
        placeholder="Nhập tên người dùng"
        value={username}
        onChangeText={(text) => {
          setUsername(text);
          setErrors({ ...errors, username: validateUsername(text) });
        }}
        autoCapitalize="none"
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
          setErrors({ ...errors, password: validatePassword(text) });
        }}
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
      {errors.password && (
        <Text style={styles.errorText}>{errors.password}</Text>
      )}

      {/* Confirm Password */}
      <Text style={styles.label}>Xác nhận mật khẩu</Text>
      <InputField
        icon={<Feather name="lock" size={18} color={TEAL} />}
        placeholder="••••••••••"
        value={confirmPassword}
        onChangeText={(text) => {
          setConfirmPassword(text);
          setErrors({
            ...errors,
            confirmPassword: validateConfirmPassword(password, text),
          });
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
      {errors.confirmPassword && (
        <Text style={styles.errorText}>{errors.confirmPassword}</Text>
      )}

      {/* Gender */}
      <Text style={styles.label}>Giới tính</Text>

      <View style={styles.genderRow}>
        {/* Nam */}
        <TouchableOpacity
          style={styles.genderOption}
          onPress={() => setGender("Male")}
        >
          <View style={styles.radioOuter}>
            {gender === "Male" && <View style={styles.radioInner} />}
          </View>
          <Text style={styles.genderText}>Nam</Text>
        </TouchableOpacity>

        {/* Nữ */}
        <TouchableOpacity
          style={styles.genderOption}
          onPress={() => setGender("Female")}
        >
          <View style={styles.radioOuter}>
            {gender === "Female" && <View style={styles.radioInner} />}
          </View>
          <Text style={styles.genderText}>Nữ</Text>
        </TouchableOpacity>
      </View>

      {/* Email */}
      <Text style={styles.label}>Email</Text>
      <InputField
        icon={<Feather name="mail" size={18} color={TEAL} />}
        placeholder="your.email@example.com"
        value={email}
        onChangeText={(text) => {
          setEmail(text);
          setErrors({ ...errors, email: validateEmail(text) });
        }}
        keyboardType="email-address"
        autoCapitalize="none"
      />
      {errors.email && <Text style={styles.errorText}>{errors.email}</Text>}

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

      <PrimaryButton
        label="Đăng ký"
        onPress={handleSignUp}
        disabled={!isValid}
      />

      {/* Login link */}
      <View style={styles.loginRow}>
        <Text style={styles.loginText}>Đã có tài khoản! </Text>
        <TouchableOpacity onPress={() => router.replace("../(auth)/sign-in")}>
          <Text style={styles.loginLink}>Đăng nhập</Text>
        </TouchableOpacity>
      </View>

      {showAlert && (
        <View style={styles.overlay}>
          <View style={styles.modal}>
            <Feather name="alert-circle" size={40} color="#EF4444" />

            <Text style={styles.modalTitle}>Thông báo</Text>
            <Text style={styles.modalMessage}>{alertMessage}</Text>

            <TouchableOpacity
              style={styles.modalButton}
              onPress={() => setShowAlert(false)}
            >
              <Text style={styles.modalButtonText}>OK</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
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
    marginBottom: 20,
  },
  label: {
    fontSize: 13,
    fontWeight: "500",
    color: "#1A1A1A",
    marginBottom: 10,
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

  genderRow: {
    flexDirection: "row",
    gap: 20,
    marginBottom: 12,
  },

  genderOption: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },

  radioOuter: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: "#B0B8C1",
    alignItems: "center",
    justifyContent: "center",
  },

  radioInner: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: TEAL,
  },

  genderText: {
    fontSize: 14,
    color: "#333",
  },

  errorText: {
    color: "#EF4444",
    fontSize: 12,
    // marginTop: 1,
    marginBottom: 15,
  },

  overlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0,0,0,0.4)",
    justifyContent: "center",
    alignItems: "center",
    zIndex: 999,
  },

  modal: {
    width: 280,
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 20,
    alignItems: "center",
  },

  modalTitle: {
    fontSize: 18,
    fontWeight: "700",
    marginTop: 10,
    marginBottom: 6,
    color: "#1A1A1A",
  },

  modalMessage: {
    fontSize: 14,
    color: "#555",
    textAlign: "center",
    marginBottom: 20,
  },

  modalButton: {
    backgroundColor: TEAL,
    paddingVertical: 10,
    paddingHorizontal: 30,
    borderRadius: 10,
  },

  modalButtonText: {
    color: "#fff",
    fontWeight: "600",
  },
});
