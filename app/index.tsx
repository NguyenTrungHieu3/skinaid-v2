import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useRef } from "react";
import {
  Animated,
  Dimensions,
  Image,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Colors } from "../constants/colors";

const { width } = Dimensions.get("window");
const SCAN_FRAME_SIZE = 160;

export default function WelcomeScreen() {
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const logoY = useRef(new Animated.Value(30)).current;
  const titleOpacity = useRef(new Animated.Value(0)).current;
  const titleY = useRef(new Animated.Value(20)).current;
  const subOpacity = useRef(new Animated.Value(0)).current;
  const btnOpacity = useRef(new Animated.Value(0)).current;
  const btnY = useRef(new Animated.Value(20)).current;
  const btnScale = useRef(new Animated.Value(1)).current;
  const insets = useSafeAreaInsets();

  useEffect(() => {
    Animated.sequence([
      Animated.parallel([
        Animated.timing(logoOpacity, {
          toValue: 1,
          duration: 700,
          useNativeDriver: true,
        }),
        Animated.timing(logoY, {
          toValue: 0,
          duration: 700,
          useNativeDriver: true,
        }),
      ]),
      Animated.parallel([
        Animated.timing(titleOpacity, {
          toValue: 1,
          duration: 500,
          useNativeDriver: true,
        }),
        Animated.timing(titleY, {
          toValue: 0,
          duration: 500,
          useNativeDriver: true,
        }),
      ]),
      Animated.timing(subOpacity, {
        toValue: 1,
        duration: 400,
        useNativeDriver: true,
      }),
      Animated.parallel([
        Animated.timing(btnOpacity, {
          toValue: 1,
          duration: 500,
          useNativeDriver: true,
        }),
        Animated.timing(btnY, {
          toValue: 0,
          duration: 500,
          useNativeDriver: true,
        }),
      ]),
    ]).start();
  }, []);

  const handleGetStarted = () => {
    router.push("/(auth)/sign-up");
  };

  return (
    <LinearGradient
      colors={[...Colors.gradientWelcome]}
      start={{ x: 0, y: 0 }}
      end={{ x: 0, y: 1 }}
      style={[
        styles.container,
        { paddingBottom: insets.bottom > 0 ? insets.bottom + 20 : 40 },
      ]}
    >
      <StatusBar barStyle="dark-content" backgroundColor={Colors.background} />

      {/* Center: logo + tên */}
      <View style={styles.centerContent}>
        <Animated.View
          style={{ opacity: logoOpacity, transform: [{ translateY: logoY }] }}
        >
          <View style={styles.scanFrame}>
            <Image
              source={require("../assets/logo.png")}
              style={styles.logoImage}
              resizeMode="contain"
            />
          </View>
        </Animated.View>

        <Animated.Text
          style={[
            styles.appName,
            { opacity: titleOpacity, transform: [{ translateY: titleY }] },
          ]}
        >
          <Text style={styles.appNameLight}>Skin</Text>
          <Text style={styles.appNameBold}>Aid</Text>
        </Animated.Text>

        <Animated.Text style={[styles.subtitle, { opacity: subOpacity }]}>
          Chào mừng bạn đến với SkinAid! Ứng dụng giúp bạn nhận diện và phân
          loại vết thương từ đó đưa ra lời khuyên chăm sóc phù hợp. Hãy bắt đầu
          hành trình chăm sóc da của bạn ngay hôm nay!
        </Animated.Text>
      </View>

      {/* Bottom: Get Started button */}
      <Animated.View
        style={[
          styles.buttonWrapper,
          { opacity: btnOpacity, transform: [{ translateY: btnY }] },
        ]}
      >
        <Animated.View style={{ transform: [{ scale: btnScale }] }}>
          <TouchableOpacity
            style={styles.button}
            activeOpacity={1}
            onPressIn={() =>
              Animated.spring(btnScale, {
                toValue: 0.96,
                useNativeDriver: true,
              }).start()
            }
            onPressOut={() =>
              Animated.spring(btnScale, {
                toValue: 1,
                useNativeDriver: true,
              }).start()
            }
            onPress={handleGetStarted}
          >
            <Text style={styles.buttonText}>Get Started</Text>
          </TouchableOpacity>
        </Animated.View>
      </Animated.View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: 80,
    paddingHorizontal: 32,
  },
  centerContent: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 16,
  },
  scanFrame: {
    width: SCAN_FRAME_SIZE,
    height: SCAN_FRAME_SIZE,
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  logoImage: { width: 200, height: 200 },
  appName: { fontSize: 36, letterSpacing: -0.5 },
  appNameLight: { color: Colors.textPrimary, fontWeight: "500" },
  appNameBold: { color: Colors.primaryLight, fontWeight: "700" },
  subtitle: {
    fontSize: 15,
    color: Colors.textMuted,
    textAlign: "center",
    lineHeight: 22,
  },
  buttonWrapper: {
    width: "100%",
    alignItems: "center",
  },
  button: {
    backgroundColor: Colors.primaryLight,
    paddingVertical: 17,
    borderRadius: 50,
    width: width - 64,
    alignItems: "center",
    shadowColor: Colors.primaryLight,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 8,
  },
  buttonText: {
    color: Colors.white,
    fontSize: 17,
    fontWeight: "600",
    letterSpacing: 0.3,
  },
});
