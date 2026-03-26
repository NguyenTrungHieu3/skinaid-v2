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

const { width } = Dimensions.get("window");
const TEAL = "#3DBFA0";
const CORNER_SIZE = 22;
const CORNER_THICKNESS = 3;
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
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />

      {/* Center: logo + tên */}
      <View style={styles.centerContent}>
        <Animated.View
          style={{ opacity: logoOpacity, transform: [{ translateY: logoY }] }}
        >
          <View style={styles.scanFrame}>
            <View style={[styles.corner, styles.cornerTL]} />
            <View style={[styles.corner, styles.cornerTR]} />
            <View style={[styles.corner, styles.cornerBL]} />
            <View style={[styles.corner, styles.cornerBR]} />
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
          Your personal skin care assistant
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
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: 80,
    paddingBottom: 52,
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
  corner: {
    position: "absolute",
    width: CORNER_SIZE,
    height: CORNER_SIZE,
    borderColor: TEAL,
  },
  cornerTL: {
    top: 0,
    left: 0,
    borderTopWidth: CORNER_THICKNESS,
    borderLeftWidth: CORNER_THICKNESS,
    borderTopLeftRadius: 4,
  },
  cornerTR: {
    top: 0,
    right: 0,
    borderTopWidth: CORNER_THICKNESS,
    borderRightWidth: CORNER_THICKNESS,
    borderTopRightRadius: 4,
  },
  cornerBL: {
    bottom: 0,
    left: 0,
    borderBottomWidth: CORNER_THICKNESS,
    borderLeftWidth: CORNER_THICKNESS,
    borderBottomLeftRadius: 4,
  },
  cornerBR: {
    bottom: 0,
    right: 0,
    borderBottomWidth: CORNER_THICKNESS,
    borderRightWidth: CORNER_THICKNESS,
    borderBottomRightRadius: 4,
  },
  logoImage: { width: 100, height: 100 },
  appName: { fontSize: 36, letterSpacing: -0.5 },
  appNameLight: { color: "#1A1A1A", fontWeight: "300" },
  appNameBold: { color: TEAL, fontWeight: "700" },
  subtitle: {
    fontSize: 15,
    color: "#9CA3AF",
    textAlign: "center",
  },
  buttonWrapper: {
    width: "100%",
    alignItems: "center",
  },
  button: {
    backgroundColor: TEAL,
    paddingVertical: 17,
    borderRadius: 50,
    width: width - 64,
    alignItems: "center",
    shadowColor: TEAL,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 8,
  },
  buttonText: {
    color: "#FFFFFF",
    fontSize: 17,
    fontWeight: "600",
    letterSpacing: 0.3,
  },
});
