// constants/colors.ts
// ─── Centralized Color Palette ─────────────────────────────────
// Tất cả màu sắc của app được quản lý tại đây.
// KHÔNG hardcode màu ở component — luôn import từ file này.

export const Colors = {
  // ── Primary ───────────────────────────────────────────────────
  primary: "#02A18D", // TEAL chính — buttons, links, accents
  primaryDark: "#007A6B", // Gradient dark / hover
  primaryLight: "#3DBFA0", // Tab active, FAB, scan button
  primaryFocused: "#2EA88A", // Focused / pressed state

  // ── Backgrounds ───────────────────────────────────────────────
  background: "#FFFFFF",
  backgroundSecondary: "#F8F9FA", // Home, list backgrounds
  backgroundTertiary: "#F3F4F6", // Input bg, chip bg
  backgroundChat: "#F0FAF8", // Chat screen bg
  backgroundChatLight: "#E8F8F6", // Chat light teal bg

  // ── Text ──────────────────────────────────────────────────────
  textPrimary: "#1A1A1A", // Headings
  textSecondary: "#111827", // Alt headings (map, etc.)
  textMuted: "#9CA3AF", // Subtitles, placeholders
  textLight: "#6B7280", // Icons, secondary info
  textDark: "#374151", // Map header text
  textLink: "#555", // Form labels muted

  // ── Borders ───────────────────────────────────────────────────
  border: "#F3F4F6", // Tab bar border, dividers
  borderLight: "#E5E7EB", // Google btn border, dividers
  borderInput: "#B0B8C1", // Input icons muted
  borderChat: "#C8EAE4", // Chat input border
  borderChatLight: "#E2F5F2", // Chat input bar top
  borderChatDate: "#D1EAE6", // Chat date separator

  // ── Status ────────────────────────────────────────────────────
  error: "#EF4444", // Validation errors
  errorLight: "#FFF5F5", // Error bubble bg
  errorBorder: "#FEBCBC", // Error bubble border
  success: "#7EFDD8", // Online dot
  warning: "#FFD97D", // Typing dot

  // ── Shadows ───────────────────────────────────────────────────
  shadow: "#000000",
  shadowTeal: "#3DBFA0",

  // ── Gradients (arrays for LinearGradient) ─────────────────────
  gradientWelcome: ["#E6FFFA", "#CCFBF1", "#FFFFFF"] as const,
  gradientHero: ["#00A693", "#007A6B"] as const,
  gradientAppName: ["#1A1A1A", "#02A18D"] as const,

  // ── Chat ──────────────────────────────────────────────────────
  chatBotBg: "#FFFFFF",
  chatUserBg: "#02A18D",
  chatDateBg: "#D9F0ED",
  chatDateText: "#6B9E97",

  // ── Google Button ─────────────────────────────────────────────
  google: "#4285F4",

  // ── Transparent / overlays ────────────────────────────────────
  overlay: "rgba(0,0,0,0.4)",
  overlayLight: "rgba(0,0,0,0.28)",
  overlayDark: "rgba(0,0,0,0.32)",
  white: "#FFFFFF",
  black: "#000000",
  transparent: "transparent",
} as const;

// ── Type helper ─────────────────────────────────────────────────
export type ColorKey = keyof typeof Colors;
