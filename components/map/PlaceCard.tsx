/**
 * PlaceCard.tsx
 * Animated bottom card that slides up when a map marker is selected.
 * Shows facility info with "Chỉ đường" and "Liên hệ" actions.
 */

import { Feather } from "@expo/vector-icons";
import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";
import { LinearGradient } from "expo-linear-gradient";
import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
  Dimensions,
  Image,
  Linking,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { NearbyPlace } from "../../services/mapService";

// ─── Icon theo category ───────────────────────────────────────────────────────
type FeatherIconName = React.ComponentProps<typeof Feather>["name"];

function getCategoryConfig(category: string): {
  icon: FeatherIconName;
  colors: [string, string];
  label: string;
} {
  const cat = (category ?? "").toLowerCase();
  if (cat.includes("hospital") || cat.includes("bệnh viện")) {
    return { icon: "activity", colors: ["#02A18D", "#007A6B"], label: "Bệnh viện" };
  }
  if (cat.includes("clinic") || cat.includes("phòng khám")) {
    return { icon: "thermometer", colors: ["#3B82F6", "#1D4ED8"], label: "Phòng khám" };
  }
  if (cat.includes("dermatology") || cat.includes("da liễu")) {
    return { icon: "user", colors: ["#8B5CF6", "#6D28D9"], label: "Da liễu" };
  }
  if (cat.includes("pharmacy") || cat.includes("nhà thuốc")) {
    return { icon: "package", colors: ["#F59E0B", "#D97706"], label: "Nhà thuốc" };
  }
  return { icon: "plus-square", colors: ["#3DBFA0", "#2EA88A"], label: "Cơ sở y tế" };
}

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const CARD_HEIGHT = 220;

interface PlaceCardProps {
  place: NearbyPlace | null;
  isLoadingRoute: boolean;
  onGetDirections: () => void;
  onDismiss: () => void;
  hospitalIconUri?: string;   // URI của hospital.png (từ useHospitalIconUri)
}

function StarRating({ rating }: { rating: number }) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  return (
    <View style={styles.starRow}>
      {[...Array(5)].map((_, i) => (
        <Feather
          key={i}
          name={i < full ? "star" : half && i === full ? "star" : "star"}
          size={12}
          color={i < full || (half && i === full) ? "#F59E0B" : "#D1D5DB"}
          style={{ marginRight: 1 }}
        />
      ))}
    </View>
  );
}

export default function PlaceCard({
  place,
  isLoadingRoute,
  onGetDirections,
  onDismiss,
  hospitalIconUri,
}: PlaceCardProps) {
  // Lấy đúng chiều cao tab bar (kể cả safe area) để không bị che
  const tabBarHeight = useBottomTabBarHeight();

  const translateY = useRef(new Animated.Value(CARD_HEIGHT)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  // Track whether card should be mounted (prevent unmounting mid-animation)
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    if (place) {
      setIsMounted(true);
      // Slide up
      Animated.parallel([
        Animated.spring(translateY, {
          toValue: 0,
          tension: 65,
          friction: 10,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      // Slide down, then unmount
      Animated.parallel([
        Animated.timing(translateY, {
          toValue: CARD_HEIGHT,
          duration: 250,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start(({ finished }) => {
        if (finished) setIsMounted(false);
      });
    }
  }, [place]);

  const handleContact = () => {
    if (!place?.phone) return;
    const phone = Platform.OS === "android" ? `tel:${place.phone}` : `telprompt:${place.phone}`;
    Linking.openURL(phone).catch(() => {});
  };

  if (!isMounted && !place) return null;

  const distanceText =
    place?.distance != null
      ? place.distance < 1000
        ? `${Math.round(place.distance)} m`
        : `${(place.distance / 1000).toFixed(1)} km`
      : "";

  return (
    <>
      {/* Backdrop tap to dismiss */}
      {place && (
        <Pressable style={styles.backdrop} onPress={onDismiss} />
      )}

      <Animated.View
        pointerEvents={place ? "auto" : "none"}  // Kông block touch khi ẩn
        style={[
          styles.card,
          { bottom: tabBarHeight },
          { transform: [{ translateY }], opacity },
        ]}
      >
        {/* Handle bar */}
        <View style={styles.handle} />

        {/* Dismiss button */}
        <Pressable style={styles.closeBtn} onPress={onDismiss}>
          <Feather name="x" size={18} color="#6B7280" />
        </Pressable>

        {/* Badge + Content */}
        <View style={styles.cardBody}>
          {/* Icon: hospital.png hoặc fallback gradient */}
          {(() => {
            const cfg = getCategoryConfig(place?.category ?? "");
            return (
              <View style={styles.iconWrapper}>
                {hospitalIconUri ? (
                  <View style={[styles.iconGrad, styles.iconImgWrap]}>
                    <Image
                      source={{ uri: hospitalIconUri }}
                      style={styles.hospitalImg}
                      resizeMode="contain"
                    />
                  </View>
                ) : (
                  <LinearGradient colors={cfg.colors} style={styles.iconGrad}>
                    <Feather name={cfg.icon} size={28} color="#FFFFFF" />
                  </LinearGradient>
                )}
                <View style={[styles.trustBadge, { backgroundColor: cfg.colors[0] }]}>
                  <Text style={styles.trustText}>{cfg.label}</Text>
                </View>
              </View>
            );
          })()}

          {/* Info */}
          <View style={styles.infoBlock}>
            <View style={styles.verifiedRow}>
              <Feather name="check-circle" size={13} color="#3DBFA0" />
              <Text style={styles.verifiedText}>Cơ sở uy tín</Text>
            </View>

            <Text style={styles.placeName} numberOfLines={2}>
              {place?.name ?? ""}
            </Text>

            <Text style={styles.address} numberOfLines={2}>
              {place?.address ?? ""}
            </Text>

            <View style={styles.metaRow}>
              {distanceText ? (
                <View style={styles.metaChip}>
                  <Feather name="map-pin" size={12} color="#3DBFA0" />
                  <Text style={styles.metaDist}>{distanceText}</Text>
                </View>
              ) : null}

              {(place?.rating ?? 0) > 0 && (
                <View style={styles.metaChip}>
                  <Feather name="star" size={12} color="#F59E0B" />
                  <Text style={styles.metaRating}>
                    {place!.rating.toFixed(1)}
                  </Text>
                </View>
              )}

              {place?.opening_hours ? (
                <View style={styles.metaChip}>
                  <Feather name="clock" size={12} color="#6B7280" />
                  <Text style={styles.metaHours} numberOfLines={1}>
                    {place.opening_hours}
                  </Text>
                </View>
              ) : null}
            </View>
          </View>
        </View>

        {/* Action buttons */}
        <View style={styles.actionRow}>
          <Pressable
            style={({ pressed }) => [
              styles.actionBtnPrimary,
              pressed && { opacity: 0.85 },
              isLoadingRoute && styles.actionBtnDisabled,
            ]}
            onPress={onGetDirections}
            disabled={isLoadingRoute}
          >
            <LinearGradient
              colors={["#3DBFA0", "#2EA88A"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.actionBtnGrad}
            >
              <Feather
                name={isLoadingRoute ? "loader" : "navigation"}
                size={16}
                color="#FFFFFF"
              />
              <Text style={styles.actionBtnPrimaryText}>
                {isLoadingRoute ? "Đang tính..." : "Chỉ đường"}
              </Text>
            </LinearGradient>
          </Pressable>

          <Pressable
            style={({ pressed }) => [
              styles.actionBtnSecondary,
              pressed && { opacity: 0.75 },
              !place?.phone && styles.actionBtnDisabled,
            ]}
            onPress={handleContact}
            disabled={!place?.phone}
          >
            <Feather name="phone" size={16} color="#3DBFA0" />
            <Text style={styles.actionBtnSecondaryText}>Liên hệ</Text>
          </Pressable>
        </View>
      </Animated.View>
    </>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    zIndex: 10,
  },
  card: {
    position: "absolute",
    // bottom is set dynamically via useBottomTabBarHeight() in component
    left: 0,
    right: 0,
    backgroundColor: "#FFFFFF",
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 28,
    zIndex: 20,
    // iOS shadow
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    // Android elevation
    elevation: 20,
  },
  handle: {
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: "#E5E7EB",
    alignSelf: "center",
    marginBottom: 12,
  },
  closeBtn: {
    position: "absolute",
    top: 16,
    right: 16,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#F3F4F6",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1,
  },
  cardBody: {
    flexDirection: "row",
    gap: 14,
    marginBottom: 18,
  },
  iconWrapper: {
    alignItems: "center",
  },
  iconGrad: {
    width: 72,
    height: 72,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  iconImgWrap: {
    backgroundColor: "#F0FBF8",
    borderWidth: 1.5,
    borderColor: "#3DBFA0",
  },
  hospitalImg: {
    width: 44,
    height: 44,
  },
  trustBadge: {
    marginTop: 6,
    backgroundColor: "#3DBFA0",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  trustText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  infoBlock: {
    flex: 1,
  },
  verifiedRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    marginBottom: 4,
  },
  verifiedText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#3DBFA0",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  placeName: {
    fontSize: 17,
    fontWeight: "800",
    color: "#111827",
    lineHeight: 22,
    marginBottom: 4,
  },
  address: {
    fontSize: 12,
    color: "#6B7280",
    lineHeight: 17,
    marginBottom: 8,
  },
  metaRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  metaChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
  },
  metaDist: {
    fontSize: 12,
    fontWeight: "700",
    color: "#3DBFA0",
  },
  metaRating: {
    fontSize: 12,
    fontWeight: "700",
    color: "#F59E0B",
  },
  metaHours: {
    fontSize: 11,
    color: "#6B7280",
    maxWidth: 130,
  },
  starRow: {
    flexDirection: "row",
  },
  actionRow: {
    flexDirection: "row",
    gap: 12,
  },
  actionBtnPrimary: {
    flex: 1,
    borderRadius: 14,
    overflow: "hidden",
  },
  actionBtnGrad: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 14,
  },
  actionBtnPrimaryText: {
    fontSize: 14,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  actionBtnSecondary: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 14,
    borderRadius: 14,
    backgroundColor: "#F0FBF8",
    borderWidth: 1.5,
    borderColor: "#3DBFA0",
  },
  actionBtnSecondaryText: {
    fontSize: 14,
    fontWeight: "700",
    color: "#3DBFA0",
  },
  actionBtnDisabled: {
    opacity: 0.5,
  },
});
