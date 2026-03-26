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

export const TEAL = "#3DBFA0";
export const TEAL_DARK = "#2EA88A";

// ─── Logo Header ───────────────────────────────────────────────
export function AuthHeader() {
  return (
    <View style={headerStyles.container}>
      <View style={headerStyles.scanFrame}>
        <View style={[headerStyles.corner, headerStyles.cornerTL]} />
        <View style={[headerStyles.corner, headerStyles.cornerTR]} />
        <View style={[headerStyles.corner, headerStyles.cornerBL]} />
        <View style={[headerStyles.corner, headerStyles.cornerBR]} />
        <Image
          source={require("../assets/logo_1.png")}
          style={headerStyles.logo}
          resizeMode="contain"
        />
      </View>
      <Text style={headerStyles.appName}>
        <Text style={headerStyles.appNameLight}>Skin</Text>
        <Text style={headerStyles.appNameBold}>Aid</Text>
      </Text>
    </View>
  );
}

const FRAME = 64;
const C = 14;
const T = 2;

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
  corner: {
    position: "absolute",
    width: C,
    height: C,
    borderColor: TEAL,
  },
  cornerTL: {
    top: 0,
    left: 0,
    borderTopWidth: T,
    borderLeftWidth: T,
    borderTopLeftRadius: 3,
  },
  cornerTR: {
    top: 0,
    right: 0,
    borderTopWidth: T,
    borderRightWidth: T,
    borderTopRightRadius: 3,
  },
  cornerBL: {
    bottom: 0,
    left: 0,
    borderBottomWidth: T,
    borderLeftWidth: T,
    borderBottomLeftRadius: 3,
  },
  cornerBR: {
    bottom: 0,
    right: 0,
    borderBottomWidth: T,
    borderRightWidth: T,
    borderBottomRightRadius: 3,
  },
  logo: { width: 42, height: 42 },
  appName: { fontSize: 22 },
  appNameLight: { color: "#1A1A1A", fontWeight: "400" },
  appNameBold: { color: "#1A1A1A", fontWeight: "700" },
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
        placeholderTextColor="#B0B8C1"
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
    borderColor: TEAL,
    borderRadius: 10,
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 14,
    height: 50,
    marginBottom: 14,
  },
  iconLeft: { marginRight: 10 },
  iconRight: { marginLeft: 8 },
  input: {
    flex: 1,
    fontSize: 15,
    color: "#1A1A1A",
  },
});

// ─── Primary Button ────────────────────────────────────────────
interface PrimaryButtonProps {
  label: string;
  onPress: () => void;
}

export function PrimaryButton({ label, onPress }: PrimaryButtonProps) {
  return (
    <TouchableOpacity
      style={btnStyles.button}
      onPress={onPress}
      activeOpacity={0.85}
    >
      <Text style={btnStyles.label}>{label}</Text>
    </TouchableOpacity>
  );
}

const btnStyles = StyleSheet.create({
  button: {
    backgroundColor: TEAL,
    borderRadius: 50,
    height: 52,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 8,
    shadowColor: TEAL,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
  },
  label: {
    color: "#FFFFFF",
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
  arrow: { color: TEAL, fontSize: 14 },
  text: { color: TEAL, fontSize: 14 },
});
