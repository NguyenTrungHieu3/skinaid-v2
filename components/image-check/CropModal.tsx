// components/image-check/CropModal.tsx
import { Feather } from "@expo/vector-icons";
import {
  SaveFormat,
  useImageManipulator,
} from "expo-image-manipulator";
import React, { useState } from "react";
import {
  ActivityIndicator,
  Dimensions,
  Image,
  Modal,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import {
  Gesture,
  GestureDetector,
  GestureHandlerRootView,
} from "react-native-gesture-handler";
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
} from "react-native-reanimated";

const { width: SCREEN_W, height: SCREEN_H } = Dimensions.get("window");
const CROP_SIZE = SCREEN_W - 64;
const TEAL = "#02A18D";

interface CropModalProps {
  visible: boolean;
  uri: string;
  onDone: (croppedUri: string) => void;
  onCancel: () => void;
}

export default function CropModal({
  visible,
  uri,
  onDone,
  onCancel,
}: CropModalProps) {
  const [imageSize, setImageSize] = useState({ w: 1, h: 1 });
  const [processing, setProcessing] = useState(false);

  // ── Animated transform values ──────────────────────────────────
  const scale = useSharedValue(1);
  const savedScale = useSharedValue(1);
  const translateX = useSharedValue(0);
  const translateY = useSharedValue(0);
  const savedTranslateX = useSharedValue(0);
  const savedTranslateY = useSharedValue(0);

  // SharedValue cho worklet access (không dùng useRef vì không accessible từ UI thread)
  const displayW = useSharedValue(SCREEN_W);
  const displayH = useSharedValue(SCREEN_W);

  // JS-side dims dùng cho render + crop math
  const [jsDims, setJsDims] = useState({ w: SCREEN_W, h: SCREEN_W });

  // ── New API: useImageManipulator ───────────────────────────────
  // Hook này phải gọi unconditionally (Rules of Hooks)
  const manipulator = useImageManipulator(uri);

  // ── Load image size khi mở modal ──────────────────────────────
  React.useEffect(() => {
    if (!uri || !visible) return;

    // Reset mọi transform khi mở lại
    scale.value = 1;
    savedScale.value = 1;
    translateX.value = 0;
    translateY.value = 0;
    savedTranslateX.value = 0;
    savedTranslateY.value = 0;

    Image.getSize(
      uri,
      (w, h) => {
        setImageSize({ w, h });
        const aspect = w / h;
        let dw: number, dh: number;
        if (aspect >= 1) {
          dh = CROP_SIZE;
          dw = CROP_SIZE * aspect;
        } else {
          dw = CROP_SIZE;
          dh = CROP_SIZE / aspect;
        }
        displayW.value = dw;
        displayH.value = dh;
        setJsDims({ w: dw, h: dh });
      },
      () => {}
    );
  }, [uri, visible]);

  // ── Pinch gesture ──────────────────────────────────────────────
  const pinchGesture = Gesture.Pinch()
    .onUpdate((e) => {
      "worklet";
      const newScale = Math.max(1, Math.min(savedScale.value * e.scale, 5));
      scale.value = newScale;

      const scaledW = displayW.value * newScale;
      const scaledH = displayH.value * newScale;
      const maxX = Math.max(0, (scaledW - CROP_SIZE) / 2);
      const maxY = Math.max(0, (scaledH - CROP_SIZE) / 2);
      translateX.value = Math.min(maxX, Math.max(-maxX, savedTranslateX.value));
      translateY.value = Math.min(maxY, Math.max(-maxY, savedTranslateY.value));
    })
    .onEnd(() => {
      "worklet";
      savedScale.value = scale.value;
      savedTranslateX.value = translateX.value;
      savedTranslateY.value = translateY.value;
    });

  // ── Pan gesture ────────────────────────────────────────────────
  const panGesture = Gesture.Pan()
    .minDistance(1)
    .onUpdate((e) => {
      "worklet";
      const s = scale.value;
      const scaledW = displayW.value * s;
      const scaledH = displayH.value * s;
      const maxX = Math.max(0, (scaledW - CROP_SIZE) / 2);
      const maxY = Math.max(0, (scaledH - CROP_SIZE) / 2);
      const rawX = savedTranslateX.value + e.translationX;
      const rawY = savedTranslateY.value + e.translationY;
      translateX.value = Math.min(maxX, Math.max(-maxX, rawX));
      translateY.value = Math.min(maxY, Math.max(-maxY, rawY));
    })
    .onEnd(() => {
      "worklet";
      savedTranslateX.value = translateX.value;
      savedTranslateY.value = translateY.value;
    });

  // ── Double tap để reset ────────────────────────────────────────
  const doubleTapGesture = Gesture.Tap()
    .numberOfTaps(2)
    .maxDuration(400)
    .maxDistance(10)
    .onStart(() => {
      "worklet";
      scale.value = withSpring(1, { damping: 15 });
      savedScale.value = 1;
      translateX.value = withSpring(0, { damping: 15 });
      translateY.value = withSpring(0, { damping: 15 });
      savedTranslateX.value = 0;
      savedTranslateY.value = 0;
    });

  // Race: gesture nào BEGAN trước thắng — không có 400ms delay như Exclusive
  // Nếu 2 ngón tay → pinch thắng. Nếu 1 ngón chạy nhanh → pan thắng. Nếu double-tap nhanh → reset thắng.
  const composedGesture = Gesture.Race(
    doubleTapGesture,
    Gesture.Simultaneous(pinchGesture, panGesture)
  );

  // ── Reset từ header button ─────────────────────────────────────
  const handleReset = () => {
    scale.value = withSpring(1, { damping: 15 });
    savedScale.value = 1;
    translateX.value = withSpring(0, { damping: 15 });
    translateY.value = withSpring(0, { damping: 15 });
    savedTranslateX.value = 0;
    savedTranslateY.value = 0;
  };

  // ── Animated style ─────────────────────────────────────────────
  const animatedImageStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: translateX.value },
      { translateY: translateY.value },
      { scale: scale.value },
    ],
  }));

  // ── Crop và lưu — dùng new API useImageManipulator ────────────
  const handleCrop = async () => {
    setProcessing(true);
    try {
      const currentScale = scale.value;
      const currentTX = translateX.value;
      const currentTY = translateY.value;
      const { w: dw, h: dh } = jsDims;

      const scaleFactorX = imageSize.w / dw;
      const scaleFactorY = imageSize.h / dh;

      const cropX =
        ((dw / 2 - currentTX) / currentScale - CROP_SIZE / 2 / currentScale) *
        scaleFactorX;
      const cropY =
        ((dh / 2 - currentTY) / currentScale - CROP_SIZE / 2 / currentScale) *
        scaleFactorY;
      const cropW = (CROP_SIZE / currentScale) * scaleFactorX;
      const cropH = (CROP_SIZE / currentScale) * scaleFactorY;

      const originX = Math.max(0, Math.round(cropX));
      const originY = Math.max(0, Math.round(cropY));
      const width = Math.min(Math.round(cropW), imageSize.w - originX);
      const height = Math.min(Math.round(cropH), imageSize.h - originY);

      // Guard: đảm bảo crop area hợp lệ
      if (width <= 0 || height <= 0) {
        console.warn("Invalid crop area, skipping crop");
        onCancel();
        return;
      }

      // ── Dùng new contextual API thay vì manipulateAsync (deprecated) ──
      // manipulateAsync() gọi native module cũ gây NoSuchMethodError trên New Architecture
      const imageRef = await manipulator
        .crop({ originX, originY, width, height })
        .renderAsync();

      const result = await imageRef.saveAsync({
        compress: 0.9,
        format: SaveFormat.JPEG,
      });

      onDone(result.uri);
    } catch (err) {
      console.error("Crop error:", err);
      onCancel();
    } finally {
      setProcessing(false);
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      statusBarTranslucent
      hardwareAccelerated
    >
      {/* GestureHandlerRootView BẮT BUỘC trong Modal trên Android
          vì Modal tạo ra một Window mới tách biệt với app root */}
      <GestureHandlerRootView style={styles.root}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onCancel} style={styles.headerBtn}>
            <Feather name="x" size={22} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Cắt ảnh</Text>
          <TouchableOpacity onPress={handleReset} style={styles.headerBtn}>
            <Feather name="refresh-cw" size={18} color="#fff" />
          </TouchableOpacity>
        </View>

        {/* Crop area — GestureDetector phải bọc Animated.View trực tiếp
            để RNGH v2 nhận diện đúng hit area trên New Architecture */}
        <GestureDetector gesture={composedGesture}>
          <Animated.View style={styles.cropContainer}>
            <Animated.View style={[styles.imageContainer, animatedImageStyle]}>
              <Image
                source={{ uri }}
                style={{ width: jsDims.w, height: jsDims.h }}
                resizeMode="cover"
              />
            </Animated.View>

            {/* Overlay mờ 4 cạnh ngoài crop frame */}
            <View style={styles.overlayContainer} pointerEvents="none">
              <View
                style={[
                  styles.dimOverlay,
                  {
                    top: 0,
                    left: 0,
                    right: 0,
                    height: (SCREEN_H - CROP_SIZE) / 2 - 60,
                  },
                ]}
              />
              <View
                style={[
                  styles.dimOverlay,
                  {
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: (SCREEN_H - CROP_SIZE) / 2 - 30,
                  },
                ]}
              />
              <View
                style={[
                  styles.dimOverlay,
                  {
                    top: (SCREEN_H - CROP_SIZE) / 2 - 60,
                    left: 0,
                    width: 32,
                    height: CROP_SIZE,
                  },
                ]}
              />
              <View
                style={[
                  styles.dimOverlay,
                  {
                    top: (SCREEN_H - CROP_SIZE) / 2 - 60,
                    right: 0,
                    width: 32,
                    height: CROP_SIZE,
                  },
                ]}
              />

              {/* Crop frame với corner brackets */}
              <View
                style={[
                  styles.cropFrame,
                  {
                    top: (SCREEN_H - CROP_SIZE) / 2 - 60,
                    left: 32,
                    width: CROP_SIZE,
                    height: CROP_SIZE,
                  },
                ]}
              >
                <View style={[styles.corner, styles.cornerTL]} />
                <View style={[styles.corner, styles.cornerTR]} />
                <View style={[styles.corner, styles.cornerBL]} />
                <View style={[styles.corner, styles.cornerBR]} />
                <View style={[styles.gridH, { top: "33.3%" }]} />
                <View style={[styles.gridH, { top: "66.6%" }]} />
                <View style={[styles.gridV, { left: "33.3%" }]} />
                <View style={[styles.gridV, { left: "66.6%" }]} />
              </View>
            </View>
          </Animated.View>
        </GestureDetector>

        {/* Hint text */}
        <View style={styles.hintRow}>
          <Feather name="info" size={12} color="rgba(255,255,255,0.5)" />
          <Text style={styles.hintText}>Chụm để zoom • Kéo để di chuyển • Nhấn 2 lần để reset</Text>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <TouchableOpacity style={styles.cancelBtn} onPress={onCancel}>
            <Text style={styles.cancelText}>Hủy</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.doneBtn, processing && styles.doneBtnDisabled]}
            onPress={handleCrop}
            disabled={processing}
          >
            {processing ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <>
                <Feather name="check" size={18} color="#fff" />
                <Text style={styles.doneText}>Xong</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      </GestureHandlerRootView>
    </Modal>
  );
}

// ── Styles ────────────────────────────────────────────────────────
const CORNER_SIZE = 24;
const CORNER_THICK = 3;

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#111",
  },
  // Header
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: 48,
    paddingBottom: 12,
    paddingHorizontal: 16,
  },
  headerBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.12)",
    alignItems: "center",
    justifyContent: "center",
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: "600",
    color: "#fff",
  },
  // Crop container
  cropContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
  },
  imageContainer: {
    alignItems: "center",
    justifyContent: "center",
  },
  overlayContainer: {
    ...StyleSheet.absoluteFillObject,
  },
  dimOverlay: {
    position: "absolute",
    backgroundColor: "rgba(0,0,0,0.55)",
  },
  cropFrame: {
    position: "absolute",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.3)",
  },
  // Corner brackets
  corner: {
    position: "absolute",
    width: CORNER_SIZE,
    height: CORNER_SIZE,
  },
  cornerTL: {
    top: -1,
    left: -1,
    borderTopWidth: CORNER_THICK,
    borderLeftWidth: CORNER_THICK,
    borderColor: TEAL,
    borderTopLeftRadius: 4,
  },
  cornerTR: {
    top: -1,
    right: -1,
    borderTopWidth: CORNER_THICK,
    borderRightWidth: CORNER_THICK,
    borderColor: TEAL,
    borderTopRightRadius: 4,
  },
  cornerBL: {
    bottom: -1,
    left: -1,
    borderBottomWidth: CORNER_THICK,
    borderLeftWidth: CORNER_THICK,
    borderColor: TEAL,
    borderBottomLeftRadius: 4,
  },
  cornerBR: {
    bottom: -1,
    right: -1,
    borderBottomWidth: CORNER_THICK,
    borderRightWidth: CORNER_THICK,
    borderColor: TEAL,
    borderBottomRightRadius: 4,
  },
  // Grid
  gridH: {
    position: "absolute",
    left: 0,
    right: 0,
    height: 1,
    backgroundColor: "rgba(255,255,255,0.15)",
  },
  gridV: {
    position: "absolute",
    top: 0,
    bottom: 0,
    width: 1,
    backgroundColor: "rgba(255,255,255,0.15)",
  },
  // Hint
  hintRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 5,
    paddingVertical: 8,
  },
  hintText: {
    fontSize: 11,
    color: "rgba(255,255,255,0.5)",
    textAlign: "center",
  },
  // Footer
  footer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 24,
    paddingBottom: 40,
    paddingTop: 8,
  },
  cancelBtn: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 12,
    backgroundColor: "rgba(255,255,255,0.1)",
  },
  cancelText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "500",
  },
  doneBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingVertical: 12,
    paddingHorizontal: 28,
    borderRadius: 12,
    backgroundColor: TEAL,
  },
  doneBtnDisabled: {
    opacity: 0.6,
  },
  doneText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "600",
  },
});
