// components/home/WoundTypeCard.tsx
import React from "react";
import { StyleSheet, Text, TouchableOpacity } from "react-native";
import { WoundType } from "../../constants/woundTypes";

interface WoundTypeCardProps {
  item: WoundType;
  onPress: (item: WoundType) => void;
}

export default function WoundTypeCard({ item, onPress }: WoundTypeCardProps) {
  return (
    <TouchableOpacity
      style={styles.card}
      onPress={() => onPress(item)}
      activeOpacity={0.75}
    >
      <Text style={styles.emoji}>{item.emoji}</Text>
      <Text style={styles.name}>{item.name}</Text>
      <Text style={styles.description}>{item.description}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: "#FFFFFF",
    borderWidth: 1.5,
    borderColor: "#3DBFA0",
    borderRadius: 14,
    padding: 14,
    margin: 5,
    alignItems: "flex-start",
    minHeight: 100,
  },
  emoji: {
    fontSize: 26,
    marginBottom: 6,
  },
  name: {
    fontSize: 15,
    fontWeight: "700",
    color: "#1A1A1A",
    marginBottom: 3,
  },
  description: {
    fontSize: 11,
    color: "#9CA3AF",
    lineHeight: 16,
  },
});
