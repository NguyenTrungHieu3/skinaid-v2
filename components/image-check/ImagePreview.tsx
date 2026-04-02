// components/image-check/ImagePreview.tsx
import React from "react";
import { Dimensions, Image, StyleSheet, Text, View } from "react-native";

const IMG_HEIGHT = Dimensions.get("window").height * 0.44;

interface ImagePreviewProps {
  uri: string;
  showWaitOverlay?: boolean; // hiện "Please wait..." khi đang loading
}

export default function ImagePreview({
  uri,
  showWaitOverlay = false,
}: ImagePreviewProps) {
  return (
    <View style={styles.container}>
      <Image source={{ uri }} style={styles.image} resizeMode="cover" />

      {/* "Please wait..." pill overlay */}
      {showWaitOverlay && (
        <View style={styles.overlayWrapper}>
          <View style={styles.waitPill}>
            <Text style={styles.waitText}>Please wait...</Text>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    borderRadius: 16,
    overflow: "hidden",
    height: IMG_HEIGHT,
    backgroundColor: "#E5E7EB",
    position: "relative",
  },
  image: {
    width: "100%",
    height: "100%",
  },
  overlayWrapper: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
  },
  waitPill: {
    paddingVertical: 10,
    paddingHorizontal: 24,
    borderRadius: 50,
    borderWidth: 1.5,
    borderColor: "#3DBFA0",
    backgroundColor: "rgba(0,0,0,0.35)",
  },
  waitText: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "500",
    letterSpacing: 0.3,
  },
});
