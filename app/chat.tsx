// app/chat.tsx
import { Feather, Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  FlatList,
  Image,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { chatbotService } from "../services/chatbotService";

const TEAL = "#02A18D";
const TEAL_DARK = "#007A6B";
const TEAL_LIGHT = "#E8F8F6";
const BOT_BG = "#FFFFFF";
const USER_BG = TEAL;

interface Message {
  id: string;
  text: string;
  sender: "bot" | "user";
  timestamp: Date;
  isError?: boolean;
}

// Giới hạn số tin nhắn người dùng mỗi phiên
const MAX_USER_MESSAGES = 4;

function formatTime(date: Date) {
  return date.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
}

function formatDate(date: Date) {
  const today = new Date();
  const isToday =
    date.getDate() === today.getDate() &&
    date.getMonth() === today.getMonth() &&
    date.getFullYear() === today.getFullYear();
  if (isToday) return "Hôm nay";
  return date.toLocaleDateString("vi-VN");
}

// ── Typing indicator component ──────────────────────────────────
function TypingIndicator() {
  const dot1 = useRef(new Animated.Value(0)).current;
  const dot2 = useRef(new Animated.Value(0)).current;
  const dot3 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animate = (dot: Animated.Value, delay: number) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(dot, { toValue: -6, duration: 300, useNativeDriver: true }),
          Animated.timing(dot, { toValue: 0, duration: 300, useNativeDriver: true }),
          Animated.delay(600 - delay),
        ])
      ).start();

    animate(dot1, 0);
    animate(dot2, 150);
    animate(dot3, 300);
  }, []);

  return (
    <View style={styles.typingContainer}>
      <Image source={require("../assets/logo_DermAid.png")} style={styles.botAvatar} />
      <View style={styles.typingBubble}>
        {[dot1, dot2, dot3].map((dot, i) => (
          <Animated.View
            key={i}
            style={[styles.typingDot, { transform: [{ translateY: dot }] }]}
          />
        ))}
      </View>
    </View>
  );
}

// ── Message bubble component ────────────────────────────────────
function MessageBubble({ message }: { message: Message }) {
  const isBot = message.sender === "bot";
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(isBot ? -15 : 15)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 300, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 300, useNativeDriver: true }),
    ]).start();
  }, []);

  return (
    <Animated.View
      style={[
        styles.messageRow,
        isBot ? styles.botRow : styles.userRow,
        { opacity: fadeAnim, transform: [{ translateX: slideAnim }] },
      ]}
    >
      {isBot && (
        <Image source={require("../assets/logo_DermAid.png")} style={styles.botAvatar} />
      )}
      <View
        style={[
          styles.bubble,
          isBot ? styles.botBubble : styles.userBubble,
          message.isError && styles.errorBubble,
        ]}
      >
        <Text style={[styles.bubbleText, isBot ? styles.botText : styles.userText]}>
          {message.text}
        </Text>
        <Text style={[styles.timeText, !isBot && styles.timeTextUser]}>
          {formatTime(message.timestamp)}
        </Text>
      </View>
    </Animated.View>
  );
}

// ── Session initialization overlay ──────────────────────────────
function SessionInitOverlay({
  status,
  onRetry,
  onBack,
}: {
  status: "loading" | "error";
  onRetry: () => void;
  onBack: () => void;
}) {
  if (status === "loading") {
    return (
      <View style={styles.initOverlay}>
        <View style={styles.initCard}>
          <ActivityIndicator size="large" color={TEAL} />
          <Text style={styles.initText}>Đang kết nối với DermAid...</Text>
          <Text style={styles.initSubText}>Vui lòng đợi trong giây lát</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.initOverlay}>
      <View style={styles.initCard}>
        <View style={styles.initErrorIcon}>
          <Feather name="wifi-off" size={32} color="#EF4444" />
        </View>
        <Text style={styles.initErrorTitle}>Không thể kết nối</Text>
        <Text style={styles.initSubText}>
          Không thể kết nối với chatbot.{"\n"}Vui lòng kiểm tra mạng và thử lại.
        </Text>
        <TouchableOpacity style={styles.retryBtn} onPress={onRetry} activeOpacity={0.8}>
          <Feather name="refresh-cw" size={16} color="#FFFFFF" />
          <Text style={styles.retryBtnText}>Thử lại</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.backBtn2} onPress={onBack} activeOpacity={0.8}>
          <Ionicons name="arrow-back" size={16} color={TEAL} />
          <Text style={styles.backBtn2Text}>Quay lại</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ── In-Memory Cache cho hội thoại Theo Vết Thương ─────────────
// Lưu lại tin nhắn và sessionId dựa trên analysisId để người dùng không bị mất chat khi back ra.
const chatSessionCache: Record<string, { sessionId: string; messages: Message[] }> = {};

// ── Main ChatScreen ─────────────────────────────────────────────
export default function ChatScreen() {
  const insets = useSafeAreaInsets();
  const { analysisId } = useLocalSearchParams<{ analysisId?: string }>();

  // ── Dynamic context (App Guide vs Wound Advisor) ──
  const quickReplies = analysisId
    ? [
        "Kết quả đánh giá này nghĩa là gì?",
        "Tôi nên chăm sóc vết thương này thế nào?",
        "Tình trạng này khi nào mới khỏi?",
        "Có cần đi gặp bác sĩ khám trực tiếp không?",
      ]
    : [
        "Cách chụp ảnh vết thương",
        "Hướng dẫn sử dụng app",
        "Xem lịch sử phân tích",
        "Tìm bệnh viện gần đây",
      ];

  const initialMessage: Message = analysisId
    ? {
        id: "welcome",
        text: "Xin chào! Tôi đã nhận được báo cáo phân tích vết thương của bạn. Tôi có thể tư vấn, hướng dẫn cách chăm sóc hoặc giải đáp thắc mắc chi tiết dựa trên kết quả báo cáo AI. Bạn cần tôi hỗ trợ gì nào? 🩺",
        sender: "bot",
        timestamp: new Date(),
      }
    : {
        id: "welcome",
        text: "Xin chào! Tôi là DermAid – trợ lý hướng dẫn sử dụng ứng dụng SkinAid. Tôi có thể giúp bạn tìm hiểu các chức năng của ứng dụng. Hãy hỏi tôi bất cứ điều gì! 🌿",
        sender: "bot",
        timestamp: new Date(),
      };

  // Không cache session — luôn probe lại khi vào chat để đảm bảo bot đang hoạt động
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showQuickReplies, setShowQuickReplies] = useState(true);
  const flatListRef = useRef<FlatList>(null);

  // ── Session state ──
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionStatus, setSessionStatus] = useState<"loading" | "ready" | "error">("loading");

  // Lưu trữ ngược lại vào cache mỗi khi có thay đổi
  useEffect(() => {
    if (analysisId && sessionId) {
      chatSessionCache[analysisId] = { sessionId, messages };
    }
  }, [analysisId, sessionId, messages]);

  // Dùng ref để cancel request khi unmount
  const isMountedRef = useRef(true);

  // ── Keyboard handling cho Android edge-to-edge ──
  const inputBarBottom = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (Platform.OS !== "android") return;

    const showSub = Keyboard.addListener("keyboardDidShow", (e) => {
      Animated.timing(inputBarBottom, {
        toValue: e.endCoordinates.height,
        duration: 250,
        useNativeDriver: false,
      }).start();
      scrollToBottom();
    });
    const hideSub = Keyboard.addListener("keyboardDidHide", () => {
      Animated.timing(inputBarBottom, {
        toValue: 0,
        duration: 250,
        useNativeDriver: false,
      }).start();
    });

    return () => {
      showSub.remove();
      hideSub.remove();
    };
  }, []);

  // ── Tạo session + probe kiểm tra bot có hoạt động không ──
  const initSession = useCallback(async () => {
    setSessionStatus("loading");
    try {
      const res = await chatbotService.createSession(analysisId || null);

      if (!isMountedRef.current) return;

      const { session_id } = res.data.data;
      setSessionId(session_id);

      // Gửi probe ẩn để kiểm tra bot có thực sự phản hồi không
      try {
        const probeRes = await chatbotService.sendMessage(session_id, '__ping__');
        if (!isMountedRef.current) return;

        // Bot phản hồi được → dùng reply làm welcome message
        const botReply = probeRes.data.data.reply;
        setMessages([
          {
            id: 'welcome',
            text: botReply,
            sender: 'bot',
            timestamp: new Date(),
          },
        ]);
        setSessionStatus('ready');
      } catch {
        if (!isMountedRef.current) return;
        // Bot không phản hồi (bị tắt, server lỗi...) → báo lỗi ngay
        console.warn('[initSession] probe failed — chatbot unavailable');
        setSessionStatus('error');
      }
    } catch (error) {
      if (!isMountedRef.current) return;
      console.error('Failed to create chatbot session:', error);
      setSessionStatus('error');
    }
  }, [analysisId]);

  useEffect(() => {
    isMountedRef.current = true;
    // Luôn probe khi mount — đảm bảo bot đang hoạt động trước khi cho nhắn tin
    initSession();

    return () => {
      // Khi thoát chat: huỷ pending state, session tự hết hạn trên Redis
      isMountedRef.current = false;
    };
  }, [initSession]);

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, []);

  // ── Gửi tin nhắn ──
  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isTyping || !sessionId) return;

      // Kiểm tra giới hạn tin nhắn — chỉ áp dụng với chat từ trang kết quả đánh giá
      if (analysisId) {
        const userCount = messages.filter((m) => m.sender === 'user').length;
        if (userCount >= MAX_USER_MESSAGES) return;
      }

      setShowQuickReplies(false);

      const userMsg: Message = {
        id: Date.now().toString(),
        text: trimmed,
        sender: "user",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInputText("");
      setIsTyping(true);
      scrollToBottom();

      try {
        const res = await chatbotService.sendMessage(sessionId, trimmed);

        if (!isMountedRef.current) return;

        const { reply } = res.data.data;

        const botMsg: Message = {
          id: (Date.now() + 1).toString(),
          text: reply,
          sender: "bot",
          timestamp: new Date(),
        };

        setIsTyping(false);
        setMessages((prev) => [...prev, botMsg]);
        scrollToBottom();
      } catch (error: any) {
        if (!isMountedRef.current) return;

        setIsTyping(false);

        const status = error?.response?.status;
        const isTimeout = error?.code === "ECONNABORTED";
        const isRateLimit = status === 429;

        if (isRateLimit) {
          // Rate limit — chỉ thông báo, vẫn cho gửi lại
          const errMsg: Message = {
            id: (Date.now() + 2).toString(),
            text: "Bạn đã gửi quá nhiều tin nhắn. Vui lòng đợi một chút rồi thử lại. ⏳",
            sender: "bot",
            timestamp: new Date(),
            isError: true,
          };
          setMessages((prev) => [...prev, errMsg]);
          scrollToBottom();
        } else if (isTimeout) {
          // Timeout — chỉ thông báo, vẫn cho gửi lại
          const errMsg: Message = {
            id: (Date.now() + 2).toString(),
            text: "Phản hồi mất quá lâu. Vui lòng thử lại với câu hỏi ngắn hơn. ⏱️",
            sender: "bot",
            timestamp: new Date(),
            isError: true,
          };
          setMessages((prev) => [...prev, errMsg]);
          scrollToBottom();
        } else {
          // Lỗi nghiêm trọng (chatbot bị tắt, server down, 4xx/5xx...)
          // → chuyển sang trạng thái lỗi, thay input bằng banner lỗi
          console.warn('[sendMessage] fatal error, switching to error state:', status, error?.message);
          setSessionStatus("error");
        }
      }
    },
    [isTyping, scrollToBottom, sessionId, messages, analysisId]
  );

  const renderItem = useCallback(
    ({ item }: { item: Message }) => <MessageBubble message={item} />,
    []
  );

  const renderDateSeparator = () => (
    <View style={styles.dateSeparator}>
      <View style={styles.dateLine} />
      <Text style={styles.dateText}>{formatDate(new Date())}</Text>
      <View style={styles.dateLine} />
    </View>
  );

  // ── Nội dung chat (FlatList + Input) ──
  const renderChatContent = () => (
    <>
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        ListHeaderComponent={renderDateSeparator}
        ListFooterComponent={
          <>
            {isTyping && <TypingIndicator />}
            {showQuickReplies && messages.length <= 1 && (
              <View style={styles.quickRepliesContainer}>
                <Text style={styles.quickRepliesLabel}>Câu hỏi gợi ý:</Text>
                <View style={styles.quickRepliesRow}>
                  {quickReplies.map((q) => (
                    <TouchableOpacity
                      key={q}
                      style={styles.quickReplyChip}
                      onPress={() => sendMessage(q)}
                      disabled={sessionStatus !== "ready"}
                    >
                      <Text style={styles.quickReplyText}>{q}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            )}
            <View style={{ height: 12 }} />
          </>
        }
        contentContainerStyle={[
          styles.messageList,
          Platform.OS === "android" && { paddingBottom: 80 + insets.bottom },
        ]}
        showsVerticalScrollIndicator={false}
        onContentSizeChange={scrollToBottom}
      />

      {/* Input bar */}
      {Platform.OS === "ios" ? (
        <View style={[styles.inputBar, { paddingBottom: Math.max(insets.bottom, 12) }]}>
          {renderInputWrapper()}
        </View>
      ) : (
        <Animated.View
          style={[
            styles.inputBar,
            {
              position: "absolute",
              left: 0,
              right: 0,
              bottom: inputBarBottom,
              paddingBottom: Math.max(insets.bottom, 12),
            },
          ]}
        >
          {renderInputWrapper()}
        </Animated.View>
      )}
    </>
  );

  const renderInputWrapper = () => {
    // Giới hạn chỉ áp dụng khi chat từ trang kết quả đánh giá (có analysisId)
    const userMsgCount = messages.filter((m) => m.sender === 'user').length;
    const isLimitReached = !!analysisId && userMsgCount >= MAX_USER_MESSAGES;
    const remaining = analysisId ? Math.max(0, MAX_USER_MESSAGES - userMsgCount) : Infinity;

    // Khi không kết nối được → hiện banner lỗi, ẩn input
    if (sessionStatus === 'error') {
      return (
        <View style={styles.errorInputBanner}>
          <Feather name="wifi-off" size={16} color="#EF4444" />
          <Text style={styles.errorInputBannerText}>
            Không thể kết nối chatbot. Vui lòng thử lại.
          </Text>
          <TouchableOpacity
            style={styles.errorRetryBtn}
            onPress={initSession}
            activeOpacity={0.8}
          >
            <Feather name="refresh-cw" size={13} color={TEAL} />
            <Text style={styles.errorRetryBtnText}>Thử lại</Text>
          </TouchableOpacity>
        </View>
      );
    }

    return (
      <>
        {isLimitReached ? (
          <View style={styles.limitBanner}>
            <Feather name="lock" size={13} color="#B45309" />
            <Text style={styles.limitBannerText}>
              Đã đạt giới hạn {MAX_USER_MESSAGES} tin nhắn trong phiên này
            </Text>
          </View>
        ) : analysisId && remaining <= 2 ? (
          <View style={styles.limitWarningBanner}>
            <Feather name="alert-circle" size={12} color="#D97706" />
            <Text style={styles.limitWarningText}>Còn {remaining} tin nhắn</Text>
          </View>
        ) : null}
        <View style={styles.inputWrapper}>
          <TextInput
            style={styles.textInput}
            placeholder={
              isLimitReached
                ? "Hết lượt gửi tin nhắn"
                : sessionStatus !== "ready"
                ? "Đang kết nối..."
                : "Nhập tin nhắn..."
            }
            placeholderTextColor="#A0AEC0"
            value={inputText}
            onChangeText={setInputText}
            multiline
            maxLength={500}
            returnKeyType="send"
            onSubmitEditing={() => sendMessage(inputText)}
            editable={!isTyping && sessionStatus === "ready" && !isLimitReached}
          />
          <TouchableOpacity
            style={[
              styles.sendBtn,
              (!inputText.trim() || isTyping || sessionStatus !== "ready" || isLimitReached) &&
                styles.sendBtnDisabled,
            ]}
            onPress={() => sendMessage(inputText)}
            disabled={!inputText.trim() || isTyping || sessionStatus !== "ready" || isLimitReached}
            activeOpacity={0.8}
          >
            <Feather
              name="send"
              size={18}
              color={
                inputText.trim() && !isTyping && sessionStatus === "ready" && !isLimitReached
                  ? "#FFFFFF"
                  : "#A0AEC0"
              }
            />
          </TouchableOpacity>
        </View>
      </>
    );
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={TEAL_DARK} translucent />

      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={22} color="#FFFFFF" />
        </TouchableOpacity>

        <View style={styles.headerCenter}>
          <Image
            source={require("../assets/logo_DermAid.png")}
            style={styles.headerAvatar}
          />
          <View>
            <Text style={styles.headerName}>DermAid</Text>
            <View style={styles.onlineRow}>
              <View
                style={[
                  styles.onlineDot,
                  isTyping && styles.onlineDotTyping,
                  sessionStatus === "error" && styles.onlineDotError,
                ]}
              />
              <Text style={styles.onlineText}>
                {sessionStatus === 'loading'
                  ? 'Đang kết nối...'
                  : sessionStatus === 'error'
                    ? 'Không hoạt động'
                    : isTyping
                      ? 'Đang trả lời...'
                      : 'Trực tuyến'}
              </Text>
            </View>
          </View>
        </View>

        <TouchableOpacity style={styles.headerAction}>
          <Feather name="more-vertical" size={22} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      {/* Session init overlay hoặc Chat content */}
      {sessionStatus === "loading" || sessionStatus === "error" ? (
        <>
          {/* Vẫn hiển thị chat phía sau (welcome message) */}
          {Platform.OS === "ios" ? (
            <KeyboardAvoidingView
              style={styles.flex}
              behavior="padding"
              keyboardVerticalOffset={insets.top + 56}
            >
              {renderChatContent()}
            </KeyboardAvoidingView>
          ) : (
            <View style={styles.flex}>{renderChatContent()}</View>
          )}
          {/* Overlay lên trên */}
          <SessionInitOverlay status={sessionStatus} onRetry={initSession} onBack={() => router.back()} />
        </>
      ) : Platform.OS === "ios" ? (
        <KeyboardAvoidingView
          style={styles.flex}
          behavior="padding"
          keyboardVerticalOffset={insets.top + 56}
        >
          {renderChatContent()}
        </KeyboardAvoidingView>
      ) : (
        <View style={styles.flex}>{renderChatContent()}</View>
      )}
    </View>
  );
}

// ── Styles ───────────────────────────────────────────────────────
const styles = StyleSheet.create({
  flex: { flex: 1 },
  container: {
    flex: 1,
    backgroundColor: "#F0FAF8",
  },

  // Header
  header: {
    backgroundColor: TEAL,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingBottom: 14,
    shadowColor: TEAL_DARK,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  backBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.15)",
  },
  headerCenter: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    marginLeft: 10,
    gap: 10,
  },
  headerAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: "rgba(255,255,255,0.6)",
    backgroundColor: "#FFFFFF",
  },
  headerName: {
    fontSize: 16,
    fontWeight: "700",
    color: "#FFFFFF",
    letterSpacing: 0.3,
  },
  onlineRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    marginTop: 1,
  },
  onlineDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: "#7EFDD8",
  },
  onlineDotTyping: {
    backgroundColor: "#FFD97D",
  },
  onlineDotError: {
    backgroundColor: "#EF4444",
  },
  onlineText: {
    fontSize: 11,
    color: "rgba(255,255,255,0.85)",
    fontWeight: "500",
  },
  headerAction: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.15)",
  },

  // Messages
  messageList: {
    paddingHorizontal: 14,
    paddingTop: 12,
  },
  messageRow: {
    flexDirection: "row",
    marginBottom: 10,
    maxWidth: "82%",
  },
  botRow: {
    alignSelf: "flex-start",
    alignItems: "flex-end",
  },
  userRow: {
    alignSelf: "flex-end",
    flexDirection: "row-reverse",
  },
  botAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    marginRight: 8,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E2F5F2",
  },
  bubble: {
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 10,
    maxWidth: "100%",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.07,
    shadowRadius: 4,
    elevation: 2,
  },
  botBubble: {
    backgroundColor: BOT_BG,
    borderBottomLeftRadius: 4,
  },
  userBubble: {
    backgroundColor: USER_BG,
    borderBottomRightRadius: 4,
  },
  errorBubble: {
    backgroundColor: "#FFF5F5",
    borderWidth: 1,
    borderColor: "#FEBCBC",
  },
  bubbleText: {
    fontSize: 14.5,
    lineHeight: 21,
  },
  botText: {
    color: "#1A202C",
  },
  userText: {
    color: "#FFFFFF",
  },
  timeText: {
    fontSize: 10,
    color: "#A0AEC0",
    textAlign: "right",
    marginTop: 4,
  },
  timeTextUser: {
    color: "rgba(255,255,255,0.65)",
  },

  // Typing indicator
  typingContainer: {
    flexDirection: "row",
    alignItems: "flex-end",
    marginBottom: 10,
    paddingHorizontal: 14,
  },
  typingBubble: {
    backgroundColor: BOT_BG,
    borderRadius: 18,
    borderBottomLeftRadius: 4,
    paddingHorizontal: 16,
    paddingVertical: 14,
    flexDirection: "row",
    gap: 5,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.07,
    shadowRadius: 4,
    elevation: 2,
  },
  typingDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: TEAL,
  },

  // Date separator
  dateSeparator: {
    flexDirection: "row",
    alignItems: "center",
    marginVertical: 16,
    gap: 10,
  },
  dateLine: {
    flex: 1,
    height: 1,
    backgroundColor: "#D1EAE6",
  },
  dateText: {
    fontSize: 12,
    color: "#6B9E97",
    fontWeight: "600",
    backgroundColor: "#D9F0ED",
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 20,
  },

  // Quick replies
  quickRepliesContainer: {
    paddingHorizontal: 14,
    marginTop: 8,
  },
  quickRepliesLabel: {
    fontSize: 12,
    color: "#6B9E97",
    fontWeight: "600",
    marginBottom: 8,
  },
  quickRepliesRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  quickReplyChip: {
    backgroundColor: "#FFFFFF",
    borderWidth: 1.5,
    borderColor: TEAL,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 7,
  },
  quickReplyText: {
    fontSize: 13,
    color: TEAL,
    fontWeight: "600",
  },

  // Input bar
  inputBar: {
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 14,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#E2F5F2",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 4,
  },
  inputWrapper: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#F0FAF8",
    borderRadius: 26,
    borderWidth: 1.5,
    borderColor: "#C8EAE4",
    paddingLeft: 16,
    paddingRight: 6,
    paddingVertical: 6,
    marginBottom: 10,
  },
  textInput: {
    flex: 1,
    fontSize: 15,
    color: "#1A202C",
    maxHeight: 100,
    paddingTop: 0,
    paddingBottom: 0,
    textAlignVertical: "center",
  },
  sendBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: TEAL,
    alignItems: "center",
    justifyContent: "center",
    marginLeft: 6,
    shadowColor: TEAL,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.4,
    shadowRadius: 6,
    elevation: 4,
  },
  sendBtnDisabled: {
    backgroundColor: "#E2E8F0",
    shadowOpacity: 0,
    elevation: 0,
  },

  // ── Session init overlay ──
  initOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(240, 250, 248, 0.92)",
    justifyContent: "center",
    alignItems: "center",
    zIndex: 10,
  },
  initCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    padding: 32,
    alignItems: "center",
    width: 280,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.1,
    shadowRadius: 24,
    elevation: 8,
  },
  initText: {
    fontSize: 16,
    fontWeight: "600",
    color: "#1A202C",
    marginTop: 16,
  },
  initSubText: {
    fontSize: 13,
    color: "#6B7280",
    marginTop: 6,
    textAlign: "center",
    lineHeight: 19,
  },
  initErrorIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: "#FEF2F2",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 8,
  },
  initErrorTitle: {
    fontSize: 17,
    fontWeight: "700",
    color: "#1A202C",
    marginTop: 4,
  },
  retryBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: TEAL,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 50,
    marginTop: 20,
    shadowColor: TEAL,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  retryBtnText: {
    fontSize: 15,
    fontWeight: "600",
    color: "#FFFFFF",
  },
  backBtn2: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 50,
    marginTop: 10,
    borderWidth: 1.5,
    borderColor: TEAL,
    backgroundColor: "transparent",
  },
  backBtn2Text: {
    fontSize: 14,
    fontWeight: "600",
    color: TEAL,
  },
  // ── Message limit banners ──
  limitBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FFFBEB',
    borderTopWidth: 1,
    borderTopColor: '#FDE68A',
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  limitBannerText: {
    fontSize: 12,
    color: '#92400E',
    fontWeight: '600',
    flex: 1,
  },
  limitWarningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FFFBEB',
    borderTopWidth: 1,
    borderTopColor: '#FEF3C7',
    paddingHorizontal: 14,
    paddingVertical: 6,
  },
  limitWarningText: {
    fontSize: 11,
    color: '#D97706',
    fontWeight: '600',
  },
  // ── Error connection banner (thay thế input khi mất kết nối) ──
  errorInputBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FEF2F2',
    borderTopWidth: 1,
    borderTopColor: '#FECACA',
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  errorInputBannerText: {
    flex: 1,
    fontSize: 12.5,
    color: '#B91C1C',
    fontWeight: '500',
  },
  errorRetryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: TEAL,
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  errorRetryBtnText: {
    fontSize: 12,
    color: TEAL,
    fontWeight: '700',
  },
});
