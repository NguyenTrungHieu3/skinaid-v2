// components/profile/ProfileHeader.tsx
import { Feather } from "@expo/vector-icons";
import React from "react";
import { Image, StyleSheet, Text, TouchableOpacity, View } from "react-native";

interface ProfileHeaderProps {
  name: string;
  memberSince: string;
  avatarUri?: string;
  onPressAvatar?: () => void;
}

export default function ProfileHeader({
  name,
  memberSince,
  avatarUri,
  onPressAvatar,
}: ProfileHeaderProps) {
  return (
    <View style={styles.container}>
      {/* Avatar */}
      <TouchableOpacity style={styles.avatarWrapper} onPress={onPressAvatar}>
        <View style={styles.avatarCircle}>
          {avatarUri ? (
            <Image source={{ uri: avatarUri }} style={styles.avatarImage} />
          ) : (
            <Feather name="user" size={48} color="rgba(255,255,255,0.9)" />
          )}
        </View>
        {/* Camera badge */}
        <View style={styles.cameraBadge}>
          <Feather name="camera" size={12} color="#3DBFA0" />
        </View>
      </TouchableOpacity>

      <Text style={styles.name}>{name}</Text>
      <Text style={styles.memberSince}>Thành viên từ {memberSince}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#3DBFA0",
    alignItems: "center",
    paddingTop: 24,
    paddingBottom: 28,
  },
  avatarWrapper: {
    position: "relative",
    marginBottom: 12,
  },
  avatarCircle: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: "rgba(255,255,255,0.25)",
    borderWidth: 3,
    borderColor: "rgba(255,255,255,0.6)",
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
  },
  avatarImage: {
    width: 90,
    height: 90,
    borderRadius: 45,
  },
  cameraBadge: {
    position: "absolute",
    bottom: 2,
    right: 2,
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1.5,
    borderColor: "#E5E7EB",
  },
  name: {
    fontSize: 20,
    fontWeight: "700",
    color: "#FFFFFF",
    marginBottom: 4,
  },
  memberSince: {
    fontSize: 13,
    color: "rgba(255,255,255,0.8)",
  },
});
