import MaskedView from "@react-native-masked-view/masked-view";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React from "react";
import {
  Image,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  TouchableOpacity,
  View,
} from "react-native";
import { Colors } from "../constants/colors";

export const TEAL = Colors.primary;
export const TEAL_DARK = Colors.primaryFocused;

// ─── Logo Header ───────────────────────────────────────────────
export function AuthHeader() {
  return (
    <View style={headerStyles.container}>
      <View style={headerStyles.scanFrame}>
        <Image
          source={require("../assets/logo_1.png")}
          style={headerStyles.logo}
          resizeMode="contain"
        />
      </View>
      <MaskedView
        style={{ flexDirection: "row" }}
        maskElement={<Text style={headerStyles.appName}>SkinAid</Text>}
      >
        <LinearGradient
          colors={[...Colors.gradientAppName]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
        >
          <Text style={[headerStyles.appName, { opacity: 0 }]}>SkinAid</Text>
        </LinearGradient>
      </MaskedView>
    </View>
  );
}

const FRAME = 64;

const headerStyles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    marginBottom: 28,
  },
  scanFrame: {
    width: FRAME,
    height: FRAME,
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  logo: { width: 72, height: 72 },
  appName: { fontSize: 22, includeFontPadding: false, fontWeight: "bold" },
});

// ─── Input Field ───────────────────────────────────────────────
interface InputFieldProps extends TextInputProps {
  icon: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export function InputField({
  icon,
  rightIcon,
  style,
  ...props
}: InputFieldProps) {
  return (
    <View style={inputStyles.wrapper}>
      <View style={inputStyles.iconLeft}>{icon}</View>
      <TextInput
        style={[inputStyles.input, style]}
        placeholderTextColor={Colors.borderInput}
        {...props}
      />
      {rightIcon && <View style={inputStyles.iconRight}>{rightIcon}</View>}
    </View>
  );
}

const inputStyles = StyleSheet.create({
  wrapper: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1.5,
    borderColor: Colors.primary,
    borderRadius: 10,
    backgroundColor: Colors.background,
    paddingHorizontal: 14,
    height: 50,
    marginBottom: 14,
  },
  iconLeft: { marginRight: 10 },
  iconRight: { marginLeft: 8 },
  input: {
    flex: 1,
    fontSize: 15,
    color: Colors.textPrimary,
  },
});

// ─── Primary Button ────────────────────────────────────────────
interface PrimaryButtonProps {
  label: string;
  onPress: () => void;
  disabled?: boolean;
}

export function PrimaryButton({
  label,
  onPress,
  disabled,
}: PrimaryButtonProps) {
  return (
    <TouchableOpacity
      style={[btnStyles.button, disabled && { opacity: 0.65 }]}
      onPress={onPress}
      activeOpacity={0.85}
      disabled={disabled}
    >
      <Text style={btnStyles.label}>{label}</Text>
    </TouchableOpacity>
  );
}

const btnStyles = StyleSheet.create({
  button: {
    backgroundColor: Colors.primary,
    borderRadius: 50,
    height: 52,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 8,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
  },
  label: {
    color: Colors.white,
    fontSize: 17,
    fontWeight: "600",
    letterSpacing: 0.3,
  },
});

// ─── Back to Login link ────────────────────────────────────────
export function BackToLogin() {
  return (
    <TouchableOpacity
      style={backStyles.row}
      onPress={() => router.replace("../(auth)/sign-in")}
    >
      <Text style={backStyles.arrow}>← </Text>
      <Text style={backStyles.text}>Quay lại trang đăng nhập</Text>
    </TouchableOpacity>
  );
}

const backStyles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    marginTop: 20,
  },
  arrow: { color: Colors.primary, fontSize: 14 },
  text: { color: Colors.primary, fontSize: 14 },
});
