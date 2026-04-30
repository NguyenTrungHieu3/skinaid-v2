// components/home/WoundTypeCard.tsx
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { WoundType } from "../../constants/woundTypes";

interface WoundTypeCardProps {
  item: WoundType;
  onPress: (item: WoundType) => void;
}

export default function WoundTypeCard({ item, onPress }: WoundTypeCardProps) {
  return (
    <TouchableOpacity
      style={styles.wrapper}
      onPress={() => onPress(item)}
      activeOpacity={0.75}
    >
      {/* Icon Badge */}
      <View style={[styles.iconBadge, { backgroundColor: item.gradientColors[0] }]}>
        <Text style={styles.emoji}>{item.emoji}</Text>
      </View>

      {/* Name */}
      <Text style={styles.name}>{item.name}</Text>

      {/* Description */}
      <Text style={styles.description} numberOfLines={2}>
        {item.description}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    flex: 1,
    margin: 6,
    borderRadius: 16,
    backgroundColor: "#FFFFFF",
    padding: 16,
    minHeight: 130,
    // Shadow iOS
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 8,
    // Shadow Android
    elevation: 3,
  },
  iconBadge: {
    width: 46,
    height: 46,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  emoji: {
    fontSize: 22,
  },
  name: {
    fontSize: 15,
    fontWeight: "700",
    color: "#1A1A1A",
    marginBottom: 4,
  },
  description: {
    fontSize: 11,
    color: "#9CA3AF",
    lineHeight: 16,
  },
});
