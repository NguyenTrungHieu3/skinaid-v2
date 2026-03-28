// components/profile/PersonalInfoView.tsx
import { Feather } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

export interface UserInfo {
  fullName: string;
  phone: string;
  birthDate: string;
  gender: string;
  address: string;
}

interface PersonalInfoViewProps {
  info: UserInfo;
  onPressEdit: () => void;
}

const FIELDS = [
  { key: "fullName", label: "Họ và tên", icon: "user" },
  { key: "phone", label: "Số điện thoại", icon: "phone" },
  { key: "birthDate", label: "Ngày sinh", icon: "calendar" },
  { key: "gender", label: "Giới tính", icon: "git-merge" },
  { key: "address", label: "Địa chỉ", icon: "map-pin" },
] as const;

export default function PersonalInfoView({
  info,
  onPressEdit,
}: PersonalInfoViewProps) {
  return (
    <View style={styles.container}>
      {/* Card header */}
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>Thông tin cơ bản</Text>
        <TouchableOpacity
          onPress={onPressEdit}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Feather name="edit-2" size={18} color="#3DBFA0" />
        </TouchableOpacity>
      </View>

      {/* Fields */}
      {FIELDS.map((field, index) => (
        <View
          key={field.key}
          style={[
            styles.fieldRow,
            index < FIELDS.length - 1 && styles.fieldBorder,
          ]}
        >
          <View style={styles.fieldLabel}>
            <Feather name={field.icon as any} size={16} color="#3DBFA0" />
            <Text style={styles.labelText}>{field.label}</Text>
          </View>
          <Text style={styles.valueText}>{info[field.key] || "N/A"}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    backgroundColor: "#F9FAFB",
    borderRadius: 14,
    overflow: "hidden",
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1A1A1A",
  },
  fieldRow: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  fieldBorder: {
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
  },
  fieldLabel: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 4,
  },
  labelText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1A1A1A",
  },
  valueText: {
    fontSize: 14,
    color: "#6B7280",
    paddingLeft: 24,
  },
});
