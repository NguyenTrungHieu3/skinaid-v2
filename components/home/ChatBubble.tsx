// components/home/ChatBubble.tsx
import { router } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
  Dimensions,
  Image,
  PanResponder,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { chatbotService } from "../../services/chatbotService";

const TEAL = "#02A18D";
const BUBBLE_SIZE = 58;
const SCREEN_WIDTH = Dimensions.get("window").width;

// All animations use useNativeDriver: false to avoid conflicts
// with PanResponder's JS-driven Animated.event.
const DRIVER = false;

type BotStatus = "checking" | "online" | "offline";

interface ChatBubbleProps {
  /** Khoảng cách từ bottom lên — truyền tabBarHeight + margin để luôn nằm trên tab bar */
  bottomOffset?: number;
}

export default function ChatBubble({ bottomOffset = 90 }: ChatBubbleProps) {
  const scaleAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const tooltipOpacity = useRef(new Animated.Value(0)).current;
  const badgePulse = useRef(new Animated.Value(1)).current;
  const [showTooltip, setShowTooltip] = useState(true);
  const [botStatus, setBotStatus] = useState<BotStatus>("checking");

  // ── Drag state ──
  const pan = useRef(new Animated.ValueXY({ x: 0, y: 0 })).current;
  const isDragging = useRef(false);

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: (_, gesture) =>
        Math.abs(gesture.dx) > 5 || Math.abs(gesture.dy) > 5,
      onPanResponderGrant: () => {
        isDragging.current = false;
        pan.setOffset({
          x: (pan.x as any)._value,
          y: (pan.y as any)._value,
        });
        pan.setValue({ x: 0, y: 0 });
        if (showTooltip) {
          Animated.timing(tooltipOpacity, {
            toValue: 0,
            duration: 200,
            useNativeDriver: DRIVER,
          }).start(() => setShowTooltip(false));
        }
      },
      onPanResponderMove: (_, gesture) => {
        if (Math.abs(gesture.dx) > 5 || Math.abs(gesture.dy) > 5) {
          isDragging.current = true;
        }
        Animated.event([null, { dx: pan.x, dy: pan.y }], {
          useNativeDriver: DRIVER,
        })(_, gesture);
      },
      onPanResponderRelease: () => {
        pan.flattenOffset();

        if (!isDragging.current) {
          router.push("/chat");
          return;
        }

        const currentX = (pan.x as any)._value;
        const bubbleScreenX = SCREEN_WIDTH - 18 - BUBBLE_SIZE / 2 + currentX;
        const snapToLeft = bubbleScreenX < SCREEN_WIDTH / 2;
        const targetX = snapToLeft ? -(SCREEN_WIDTH - 18 - BUBBLE_SIZE - 18) : 0;

        Animated.spring(pan.x, {
          toValue: targetX,
          tension: 60,
          friction: 8,
          useNativeDriver: DRIVER,
        }).start();
      },
    })
  ).current;

  // ── Probe chatbot health ────────────────────────────────
  useEffect(() => {
    let cancelled = false;

    async function checkBotHealth() {
      try {
        // Chỉ kiểm tra createSession — đủ để biết server có thể tiếp nhận kết nối không
        // (không gửi message để tránh timeout LLM gây false-negative)
        await chatbotService.createSession(null);
        if (cancelled) return;
        setBotStatus('online');
      } catch {
        if (cancelled) return;
        setBotStatus('offline');
      }
    }

    // Kiểm tra ngay khi mount
    checkBotHealth();

    // Re-check mỗi 60 giây — badge tự đổi khi bot bật/tắt
    const interval = setInterval(checkBotHealth, 60_000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  // ── Badge nhấp nháy khi đang kiểm tra ──────────────────────────
  useEffect(() => {
    if (botStatus !== "checking") {
      badgePulse.setValue(1);
      return;
    }
    const anim = Animated.loop(
      Animated.sequence([
        Animated.timing(badgePulse, { toValue: 0.3, duration: 500, useNativeDriver: DRIVER }),
        Animated.timing(badgePulse, { toValue: 1, duration: 500, useNativeDriver: DRIVER }),
      ])
    );
    anim.start();
    return () => anim.stop();
  }, [botStatus]);

  // ── Entry + pulse animation ─────────────────────────────────────
  useEffect(() => {
    Animated.spring(scaleAnim, {
      toValue: 1,
      tension: 60,
      friction: 7,
      useNativeDriver: DRIVER,
      delay: 800,
    }).start();

    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.08, duration: 900, useNativeDriver: DRIVER }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 900, useNativeDriver: DRIVER }),
      ])
    );
    pulse.start();

    const tooltipTimeout = setTimeout(() => {
      Animated.timing(tooltipOpacity, { toValue: 1, duration: 400, useNativeDriver: DRIVER }).start();
    }, 1200);

    const hideTimeout = setTimeout(() => {
      Animated.timing(tooltipOpacity, { toValue: 0, duration: 400, useNativeDriver: DRIVER })
        .start(() => setShowTooltip(false));
    }, 5200);

    return () => {
      pulse.stop();
      clearTimeout(tooltipTimeout);
      clearTimeout(hideTimeout);
    };
  }, []);

  // Badge color: vàng khi checking, xanh khi online, đỏ khi offline
  const badgeColor =
    botStatus === "online"  ? "#2ECC71" :
    botStatus === "offline" ? "#EF4444" :
                              "#F59E0B";

  return (
    <Animated.View
      style={[
        styles.wrapper,
        {
          bottom: bottomOffset,
          transform: [
            { scale: scaleAnim },
            { translateX: pan.x },
            { translateY: pan.y },
          ],
        },
      ]}
      {...panResponder.panHandlers}
    >
      {/* Tooltip */}
      {showTooltip && (
        <Animated.View style={[styles.tooltip, { opacity: tooltipOpacity }]}>
          <Text style={styles.tooltipText}>
            Xin chào! Tôi có thể{"\n"}giúp gì cho bạn? 👋
          </Text>
          <View style={styles.tooltipArrow} />
        </Animated.View>
      )}

      {/* Ripple ring */}
      <Animated.View style={[styles.ripple, { transform: [{ scale: pulseAnim }] }]} />

      {/* Main button */}
      <View style={styles.bubble}>
        <Image
          source={require("../../assets/logo_DermAid.png")}
          style={styles.icon}
          resizeMode="contain"
        />
      </View>

      {/* Status badge — xanh/đỏ/vàng */}
      <Animated.View
        style={[
          styles.onlineBadge,
          { backgroundColor: badgeColor, opacity: badgePulse },
        ]}
      />
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    position: "absolute",
    right: 18,
    alignItems: "center",
  },
  ripple: {
    position: "absolute",
    width: 60,
    height: 58,
    borderRadius: 34,
    backgroundColor: "rgba(2, 161, 141, 0.2)",
  },
  bubble: {
    width: BUBBLE_SIZE,
    height: BUBBLE_SIZE,
    borderRadius: 29,
    backgroundColor: TEAL,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: TEAL,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.45,
    shadowRadius: 12,
    elevation: 10,
  },
  icon: {
    width: 50,
    height: 50,
  },
  onlineBadge: {
    position: "absolute",
    top: 2,
    right: 2,
    width: 13,
    height: 13,
    borderRadius: 7,
    borderWidth: 2,
    borderColor: "#FFFFFF",
  },
  tooltip: {
    position: "absolute",
    bottom: 70,
    right: 0,
    backgroundColor: "#FFFFFF",
    borderColor: "#02A18D",
    borderWidth: 1,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 10,
    width: 180,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 10,
    elevation: 6,
  },
  tooltipText: {
    fontSize: 13,
    color: "#1A202C",
    fontWeight: "500",
    lineHeight: 19,
  },
  tooltipArrow: {
    position: "absolute",
    bottom: -8,
    right: 20,
    width: 0,
    height: 0,
    borderLeftWidth: 8,
    borderRightWidth: 8,
    borderTopWidth: 9,
    borderLeftColor: "transparent",
    borderRightColor: "transparent",
    borderTopColor: "#FFFFFF",
  },
});
