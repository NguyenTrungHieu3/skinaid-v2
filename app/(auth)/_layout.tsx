import { AuthProvider } from "@/context/AuthContext";
import { Stack } from "expo-router";

export default function AuthLayout() {
  return (
    <AuthProvider>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="sign-in" />
        <Stack.Screen name="sign-up" />
        <Stack.Screen name="forgot-password" />
        <Stack.Screen name="reset-password" />
        <Stack.Screen name="change-password" />
      </Stack>
    </AuthProvider>
  );
}
