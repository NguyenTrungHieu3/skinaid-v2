// components/profile/PersonalInfoEdit.tsx
import { Feather } from "@expo/vector-icons";
import React, { useState } from "react";
import {
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { UserInfo } from "./PersonalInfoView";

interface PersonalInfoEditProps {
  info: UserInfo;
  onSave: (updated: UserInfo) => void;
  onCancel: () => void;
}

const FIELDS: {
  key: keyof UserInfo;
  label: string;
  icon: string;
  keyboardType?: "default" | "phone-pad";
  placeholder: string;
}[] = [
  {
    key: "fullName",
    label: "Họ và tên",
    icon: "user",
    placeholder: "Nhập họ và tên",
  },
  {
    key: "phone",
    label: "Số điện thoại",
    icon: "phone",
    keyboardType: "phone-pad",
    placeholder: "Nhập số điện thoại",
  },
  {
    key: "birthDate",
    label: "Ngày sinh",
    icon: "calendar",
    placeholder: "dd/mm/yyyy",
  },
  {
    key: "gender",
    label: "Giới tính",
    icon: "git-merge",
    placeholder: "Nam / Nữ / Khác",
  },
  {
    key: "address",
    label: "Địa chỉ",
    icon: "map-pin",
    placeholder: "Nhập địa chỉ",
  },
];

export default function PersonalInfoEdit({
  info,
  onSave,
  onCancel,
}: PersonalInfoEditProps) {
  const [form, setForm] = useState<UserInfo>({ ...info });

  const handleChange = (key: keyof UserInfo, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <View style={styles.container}>
      {/* Card header */}
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>Thông tin cơ bản</Text>
        <TouchableOpacity
          onPress={onCancel}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Feather name="edit-2" size={18} color="#3DBFA0" />
        </TouchableOpacity>
      </View>

      {/* Editable fields */}
      {FIELDS.map((field) => (
        <View key={field.key} style={styles.fieldRow}>
          <View style={styles.fieldLabel}>
            <Feather name={field.icon as any} size={15} color="#3DBFA0" />
            <Text style={styles.labelText}>{field.label}</Text>
          </View>
          <TextInput
            style={styles.input}
            value={form[field.key]}
            onChangeText={(v) => handleChange(field.key, v)}
            placeholder={field.placeholder}
            placeholderTextColor="#B0B8C1"
            keyboardType={field.keyboardType || "default"}
          />
        </View>
      ))}

      {/* Save button */}
      <TouchableOpacity style={styles.saveBtn} onPress={() => onSave(form)}>
        <Text style={styles.saveBtnText}>Lưu thay đổi</Text>
      </TouchableOpacity>
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
    paddingTop: 10,
    paddingBottom: 4,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
  },
  fieldLabel: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 6,
  },
  labelText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1A1A1A",
  },
  input: {
    height: 40,
    borderWidth: 1.5,
    borderColor: "#3DBFA0",
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 14,
    color: "#1A1A1A",
    backgroundColor: "#FFFFFF",
    marginBottom: 6,
  },
  saveBtn: {
    margin: 16,
    backgroundColor: "#3DBFA0",
    borderRadius: 50,
    height: 48,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#3DBFA0",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  saveBtnText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
});
