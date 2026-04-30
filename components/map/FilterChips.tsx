/**
 * FilterChips.tsx
 * Horizontal scrollable filter chips for selecting medical facility category.
 * apiCategory values match OpenAPI NearbyPlacesRequest schema (healthcare.xxx format).
 */

import React, { useRef } from "react";
import {
  Animated,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { Feather } from "@expo/vector-icons";

export type FilterKey =
  | "nearest"
  | "hospital"
  | "clinic"
  | "dermatology"
  | "pharmacy";

export interface FilterOption {
  key: FilterKey;
  label: string;
  icon: keyof typeof Feather.glyphMap;
  apiCategory: string; // value sent to nearby-places API
}

// Category values per OpenAPI spec: "healthcare.hospital", "healthcare.clinic", etc.
export const FILTER_OPTIONS: FilterOption[] = [
  {
    key: "nearest",
    label: "Gần nhất",
    icon: "navigation",
    apiCategory: "healthcare.hospital", // default broad search
  },
  {
    key: "hospital",
    label: "Bệnh viện",
    icon: "activity",
    apiCategory: "healthcare.hospital",
  },
  {
    key: "clinic",
    label: "Phòng khám",
    icon: "briefcase",
    apiCategory: "healthcare.clinic",
  },
  {
    key: "dermatology",
    label: "Da liễu",
    icon: "heart",
    apiCategory: "healthcare.clinic",
  },
  {
    key: "pharmacy",
    label: "Nhà thuốc",
    icon: "plus-square",
    apiCategory: "healthcare.pharmacy",
  },
];

interface FilterChipsProps {
  selected: FilterKey;
  onChange: (key: FilterKey, apiCategory: string) => void;
}

function Chip({
  option,
  isActive,
  onPress,
}: {
  option: FilterOption;
  isActive: boolean;
  onPress: () => void;
}) {
  const scale = useRef(new Animated.Value(1)).current;

  const handlePress = () => {
    Animated.sequence([
      Animated.timing(scale, { toValue: 0.92, duration: 80, useNativeDriver: true }),
      Animated.timing(scale, { toValue: 1, duration: 120, useNativeDriver: true }),
    ]).start();
    onPress();
  };

  return (
    <Animated.View style={{ transform: [{ scale }] }}>
      <Pressable
        onPress={handlePress}
        style={[styles.chip, isActive && styles.chipActive]}
        accessibilityRole="button"
        accessibilityLabel={option.label}
        accessibilityState={{ selected: isActive }}
      >
        <Feather
          name={option.icon}
          size={13}
          color={isActive ? "#FFFFFF" : "#4B5563"}
          style={styles.chipIcon}
        />
        <Text style={[styles.chipText, isActive && styles.chipTextActive]}>
          {option.label}
        </Text>
      </Pressable>
    </Animated.View>
  );
}

export default function FilterChips({ selected, onChange }: FilterChipsProps) {
  return (
    <View style={styles.wrapper}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {FILTER_OPTIONS.map((opt) => (
          <Chip
            key={opt.key}
            option={opt}
            isActive={selected === opt.key}
            onPress={() => onChange(opt.key, opt.apiCategory)}
          />
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { paddingVertical: 10 },
  scrollContent: { paddingHorizontal: 16, gap: 8 },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: "#F3F4F6",
    borderWidth: 1.5,
    borderColor: "#E5E7EB",
  },
  chipActive: {
    backgroundColor: "#3DBFA0",
    borderColor: "#3DBFA0",
    shadowColor: "#3DBFA0",
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.35,
    shadowRadius: 6,
    elevation: 4,
  },
  chipIcon: { marginRight: 5 },
  chipText: { fontSize: 13, fontWeight: "600", color: "#4B5563" },
  chipTextActive: { color: "#FFFFFF" },
});
