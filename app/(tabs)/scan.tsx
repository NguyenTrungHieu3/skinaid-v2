// app/(tabs)/scan.tsx
import { router } from "expo-router";
import React, { useRef, useState } from "react";
import { Alert, Dimensions, StyleSheet, View } from "react-native";

import { CameraType, CameraView, useCameraPermissions } from "expo-camera";
import * as ImagePicker from "expo-image-picker";

import NoCameraPermission from "../../components/scan/NoCameraPermission";
import ScanBottomBar from "../../components/scan/ScanBottomBar";
import ScanFrame from "../../components/scan/ScanFrame";
import ScanTopBar from "../../components/scan/ScanTopBar";

const { height: SCREEN_HEIGHT } = Dimensions.get("window");

export default function ScanScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [facing] = useState<CameraType>("back");
  const [isCapturing, setIsCapturing] = useState(false);
  const cameraRef = useRef<CameraView>(null);

  // Chưa có response quyền
  if (!permission) return <View style={styles.container} />;

  // Chưa cấp quyền camera
  if (!permission.granted) {
    return <NoCameraPermission onRequestPermission={requestPermission} />;
  }

  // Chụp ảnh
  const handleCapture = async () => {
    if (!cameraRef.current || isCapturing) return;
    setIsCapturing(true);
    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.85,
        base64: false,
      });
      console.log("Photo taken:", photo?.uri);
      // TODO: router.push({ pathname: "/(app)/result", params: { uri: photo.uri } });
    } catch {
      Alert.alert("Lỗi", "Không thể chụp ảnh. Vui lòng thử lại.");
    } finally {
      setIsCapturing(false);
    }
  };

  // Chọn ảnh từ thư viện
  const handlePickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") {
      Alert.alert(
        "Cần quyền truy cập",
        "Vui lòng cho phép truy cập thư viện ảnh trong Cài đặt."
      );
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.85,
    });
    if (!result.canceled && result.assets.length > 0) {
      console.log("Image picked:", result.assets[0].uri);
      // TODO: router.push({ pathname: "/(app)/result", params: { uri: result.assets[0].uri } });
    }
  };

  return (
    <View style={styles.container}>
      {/* Full-screen camera */}
      <CameraView
        ref={cameraRef}
        style={StyleSheet.absoluteFill}
        facing={facing}
      />

      {/* Dim overlay top */}
      <View style={styles.overlayTop} />

      {/* Dim overlay bottom */}
      <View style={styles.overlayBottom} />

      {/* Top bar: X + "Chụp hình" */}
      <ScanTopBar title="Chụp hình" onClose={() => router.back()} />

      {/* Scan frame centered */}
      <View style={styles.frameWrapper} pointerEvents="none">
        <ScanFrame />
      </View>

      {/* Bottom controls: gallery + shutter */}
      <ScanBottomBar
        onCapture={handleCapture}
        onPickImage={handlePickImage}
        isCapturing={isCapturing}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#000",
  },
  overlayTop: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: SCREEN_HEIGHT * 0.12,
    backgroundColor: "rgba(0,0,0,0.28)",
    zIndex: 1,
  },
  overlayBottom: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    height: SCREEN_HEIGHT * 0.2,
    backgroundColor: "rgba(0,0,0,0.32)",
    zIndex: 1,
  },
  frameWrapper: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
    zIndex: 2,
  },
});
