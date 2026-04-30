import { Stack } from "expo-router";

// AuthProvider đã wrap ở root _layout.tsx → KHÔNG wrap lại ở đây
export default function AuthLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="sign-in" />
      <Stack.Screen name="sign-up" />
      <Stack.Screen name="forgot-password" />
      <Stack.Screen name="reset-password" />
      <Stack.Screen name="change-password" />
    </Stack>
  );
}
