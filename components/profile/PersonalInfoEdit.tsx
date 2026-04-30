// components/profile/PersonalInfoEdit.tsx
import { Feather, MaterialCommunityIcons } from "@expo/vector-icons";
import React, { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Modal,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { authService } from "../../services/authService";
import { validatePhone } from "../../utils/validation";
import { UserInfo } from "./PersonalInfoView";

const TEAL = "#02A18D";

interface PersonalInfoEditProps {
  info: UserInfo;
  onSave: (updated: UserInfo) => void;
  onCancel: () => void;
}

const TEXT_FIELDS: {
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
    placeholder: "Nhập số điện thoại (VD: 0912345678)",
  },
];

// ── Helpers ──────────────────────────────────────────────

/** dd/mm/yyyy → yyyy-mm-dd for API */
function toISODate(dateStr: string): string | undefined {
  if (!dateStr) return undefined;
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return dateStr;
  if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateStr)) {
    const [dd, mm, yyyy] = dateStr.split("/");
    return `${yyyy}-${mm}-${dd}`;
  }
  return undefined;
}

/** Auto-format date input: 2 digits → add /, max dd/mm/yyyy */
function formatDateInput(raw: string, prev: string): string {
  // Only keep digits
  let digits = raw.replace(/[^\d]/g, "");
  if (digits.length > 8) digits = digits.slice(0, 8);

  // Detect if user is deleting (backspace)
  if (raw.length < prev.length) {
    // If previous ended with "/" and user deleted, remove the slash too
    if (prev.endsWith("/") && raw === prev.slice(0, -1)) {
      return raw.slice(0, -1);
    }
    return raw;
  }

  // Build formatted string
  let result = "";
  for (let i = 0; i < digits.length; i++) {
    result += digits[i];
    if ((i === 1 || i === 3) && i < digits.length - 1) {
      result += "/";
    }
  }
  return result;
}

/** Validate date: valid format, valid calendar date, not in the future */
function validateBirthDateFull(date: string): string {
  if (!date) return "";

  const match = date.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!match) return "Định dạng: dd/mm/yyyy";

  const day = parseInt(match[1], 10);
  const month = parseInt(match[2], 10);
  const year = parseInt(match[3], 10);

  if (month < 1 || month > 12) return "Tháng không hợp lệ";
  if (day < 1 || day > 31) return "Ngày không hợp lệ";

  const d = new Date(year, month - 1, day);
  if (d.getFullYear() !== year || d.getMonth() !== month - 1 || d.getDate() !== day) {
    return "Ngày không tồn tại";
  }
  if (d > new Date()) return "Ngày sinh không thể ở tương lai";

  return "";
}

/** Map gender display → API value */
function genderToApi(display: string): string | undefined {
  if (display === "Nam") return "Male";
  if (display === "Nữ") return "Female";
  return display || undefined;
}

// ── Calendar Picker ──────────────────────────────────────

const MONTHS_VI = [
  "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4",
  "Tháng 5", "Tháng 6", "Tháng 7", "Tháng 8",
  "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12",
];
const WEEKDAYS = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month + 1, 0).getDate();
}

function CalendarPicker({
  visible,
  initialDate,
  onSelect,
  onClose,
}: {
  visible: boolean;
  initialDate?: string;
  onSelect: (dateStr: string) => void;
  onClose: () => void;
}) {
  const today = new Date();

  // Parse initial date dd/mm/yyyy
  let initYear = today.getFullYear() - 20;
  let initMonth = today.getMonth();
  let initDay = today.getDate();
  if (initialDate) {
    const m = initialDate.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (m) {
      initDay = parseInt(m[1], 10);
      initMonth = parseInt(m[2], 10) - 1;
      initYear = parseInt(m[3], 10);
    }
  }

  const [viewYear, setViewYear] = useState(initYear);
  const [viewMonth, setViewMonth] = useState(initMonth);
  const [selectedDay, setSelectedDay] = useState(initDay);
  const [showYearPicker, setShowYearPicker] = useState(false);

  const daysInMonth = getDaysInMonth(viewYear, viewMonth);
  const firstDayOfWeek = new Date(viewYear, viewMonth, 1).getDay();

  const prevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11);
      setViewYear(viewYear - 1);
    } else {
      setViewMonth(viewMonth - 1);
    }
  };

  const nextMonth = () => {
    const nextDate = new Date(viewYear, viewMonth + 1, 1);
    if (nextDate > today) return; // Don't go past current month
    if (viewMonth === 11) {
      setViewMonth(0);
      setViewYear(viewYear + 1);
    } else {
      setViewMonth(viewMonth + 1);
    }
  };

  const handleDayPress = (day: number) => {
    const selected = new Date(viewYear, viewMonth, day);
    if (selected > today) return; // Can't select future dates
    setSelectedDay(day);
  };

  const handleConfirm = () => {
    const dd = String(selectedDay).padStart(2, "0");
    const mm = String(viewMonth + 1).padStart(2, "0");
    onSelect(`${dd}/${mm}/${viewYear}`);
    onClose();
  };

  const isFutureDay = (day: number) => {
    return new Date(viewYear, viewMonth, day) > today;
  };

  const isSelected = (day: number) => {
    return day === selectedDay;
  };

  // Year picker range
  const currentYear = today.getFullYear();
  const years = [];
  for (let y = currentYear; y >= currentYear - 100; y--) {
    years.push(y);
  }

  return (
    <Modal visible={visible} transparent animationType="fade">
      <TouchableOpacity style={calStyles.overlay} activeOpacity={1} onPress={onClose}>
        <TouchableOpacity style={calStyles.container} activeOpacity={1}>
          {/* Header: month/year navigation */}
          <View style={calStyles.header}>
            <TouchableOpacity onPress={prevMonth} style={calStyles.navBtn}>
              <Feather name="chevron-left" size={20} color={TEAL} />
            </TouchableOpacity>

            <TouchableOpacity onPress={() => setShowYearPicker(!showYearPicker)}>
              <Text style={calStyles.headerTitle}>
                {MONTHS_VI[viewMonth]} {viewYear}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={nextMonth} style={calStyles.navBtn}>
              <Feather name="chevron-right" size={20} color={TEAL} />
            </TouchableOpacity>
          </View>

          {showYearPicker ? (
            <View style={calStyles.yearGrid}>
              {years.slice(0, 20).map((y) => (
                <TouchableOpacity
                  key={y}
                  style={[
                    calStyles.yearBtn,
                    y === viewYear && calStyles.yearBtnActive,
                  ]}
                  onPress={() => {
                    setViewYear(y);
                    setShowYearPicker(false);
                  }}
                >
                  <Text
                    style={[
                      calStyles.yearText,
                      y === viewYear && calStyles.yearTextActive,
                    ]}
                  >
                    {y}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          ) : (
            <>
              {/* Weekday labels */}
              <View style={calStyles.weekRow}>
                {WEEKDAYS.map((d) => (
                  <Text key={d} style={calStyles.weekLabel}>{d}</Text>
                ))}
              </View>

              {/* Day grid */}
              <View style={calStyles.dayGrid}>
                {/* Empty cells for offset */}
                {Array.from({ length: firstDayOfWeek }).map((_, i) => (
                  <View key={`empty-${i}`} style={calStyles.dayCell} />
                ))}

                {Array.from({ length: daysInMonth }).map((_, i) => {
                  const day = i + 1;
                  const future = isFutureDay(day);
                  const selected = isSelected(day);
                  return (
                    <TouchableOpacity
                      key={day}
                      style={[
                        calStyles.dayCell,
                        selected && calStyles.dayCellSelected,
                      ]}
                      onPress={() => handleDayPress(day)}
                      disabled={future}
                    >
                      <Text
                        style={[
                          calStyles.dayText,
                          future && calStyles.dayTextDisabled,
                          selected && calStyles.dayTextSelected,
                        ]}
                      >
                        {day}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            </>
          )}

          {/* Actions */}
          <View style={calStyles.actions}>
            <TouchableOpacity onPress={onClose} style={calStyles.cancelBtn}>
              <Text style={calStyles.cancelText}>Hủy</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={handleConfirm} style={calStyles.confirmBtn}>
              <Text style={calStyles.confirmText}>Chọn</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </TouchableOpacity>
    </Modal>
  );
}

// ── Main Component ───────────────────────────────────────

export default function PersonalInfoEdit({
  info,
  onSave,
  onCancel,
}: PersonalInfoEditProps) {
  const [form, setForm] = useState<UserInfo>({ ...info });
  const [fieldErrors, setFieldErrors] = useState<Partial<UserInfo>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [showCalendar, setShowCalendar] = useState(false);
  const [showGenderPicker, setShowGenderPicker] = useState(false);

  const handleChange = (key: keyof UserInfo, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setFieldErrors((prev) => ({ ...prev, [key]: "" }));
  };

  /** Auto-format date on typing */
  const handleDateChange = (raw: string) => {
    const formatted = formatDateInput(raw, form.birthDate);
    setForm((prev) => ({ ...prev, birthDate: formatted }));
    setFieldErrors((prev) => ({ ...prev, birthDate: "" }));
  };

  const validate = (): boolean => {
    const errs: Partial<UserInfo> = {};

    if (!form.fullName.trim()) errs.fullName = "Họ và tên không được để trống";
    if (form.phone) {
      const phoneErr = validatePhone(form.phone);
      if (phoneErr) errs.phone = phoneErr;
    }
    if (form.birthDate) {
      const dateErr = validateBirthDateFull(form.birthDate);
      if (dateErr) errs.birthDate = dateErr;
    }

    setFieldErrors(errs);
    return Object.values(errs).every((e) => !e);
  };

  const handleSave = async () => {
    if (!validate()) return;

    try {
      setIsSaving(true);
      const res = await authService.updateProfile({
        full_name: form.fullName,
        phone: form.phone || undefined,
        date_of_birth: toISODate(form.birthDate),
        gender: genderToApi(form.gender),
        address: form.address || undefined,
      });

      const data = res.data?.data || res.data;

      const updated: UserInfo = {
        fullName: data.full_name || form.fullName,
        phone: data.phone || form.phone,
        birthDate: data.date_of_birth
          ? (() => {
              const d = new Date(data.date_of_birth);
              const dd = String(d.getDate()).padStart(2, "0");
              const mm = String(d.getMonth() + 1).padStart(2, "0");
              return `${dd}/${mm}/${d.getFullYear()}`;
            })()
          : form.birthDate,
        gender: data.gender_display || data.gender || form.gender,
        address: data.address || form.address,
      };

      onSave(updated);
    } catch (e: any) {
      const msg =
        e?.response?.data?.message ||
        "Cập nhật thất bại. Vui lòng thử lại.";
      Alert.alert("Lỗi", msg);
    } finally {
      setIsSaving(false);
    }
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
          <Feather name="x" size={18} color="#6B7280" />
        </TouchableOpacity>
      </View>

      {/* Text fields: Họ và tên, Số điện thoại */}
      {TEXT_FIELDS.map((field) => (
        <View key={field.key} style={styles.fieldRow}>
          <View style={styles.fieldLabel}>
            <Feather name={field.icon as any} size={15} color={TEAL} />
            <Text style={styles.labelText}>{field.label}</Text>
          </View>
          <TextInput
            style={[
              styles.input,
              !!fieldErrors[field.key] && styles.inputError,
            ]}
            value={form[field.key]}
            onChangeText={(v) => handleChange(field.key, v)}
            placeholder={field.placeholder}
            placeholderTextColor="#B0B8C1"
            keyboardType={field.keyboardType || "default"}
          />
          {!!fieldErrors[field.key] && (
            <Text style={styles.errorText}>{fieldErrors[field.key]}</Text>
          )}
        </View>
      ))}

      {/* ── Ngày sinh field ── */}
      <View style={styles.fieldRow}>
        <View style={styles.fieldLabel}>
          <Feather name="calendar" size={15} color={TEAL} />
          <Text style={styles.labelText}>Ngày sinh</Text>
        </View>
        <View style={styles.dateRow}>
          <TextInput
            style={[
              styles.input,
              { flex: 1 },
              !!fieldErrors.birthDate && styles.inputError,
            ]}
            value={form.birthDate}
            onChangeText={handleDateChange}
            placeholder="dd/mm/yyyy"
            placeholderTextColor="#B0B8C1"
            keyboardType="number-pad"
            maxLength={10}
          />
          <TouchableOpacity
            style={styles.calendarBtn}
            onPress={() => setShowCalendar(true)}
          >
            <Feather name="calendar" size={18} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
        {!!fieldErrors.birthDate && (
          <Text style={styles.errorText}>{fieldErrors.birthDate}</Text>
        )}
      </View>

      {/* ── Giới tính field ── */}
      <View style={styles.fieldRow}>
        <View style={styles.fieldLabel}>
          <MaterialCommunityIcons name="gender-male-female" size={17} color={TEAL} />
          <Text style={styles.labelText}>Giới tính</Text>
        </View>
        <View style={styles.genderRow}>
          {(
            [
              { label: "Nam", icon: "gender-male" as const },
              { label: "Nữ", icon: "gender-female" as const },
            ] as const
          ).map(({ label, icon }) => (
            <TouchableOpacity
              key={label}
              style={[
                styles.genderOption,
                form.gender === label && styles.genderOptionActive,
              ]}
              onPress={() => handleChange("gender", label)}
            >
              <MaterialCommunityIcons
                name={icon}
                size={20}
                color={form.gender === label ? TEAL : "#9CA3AF"}
              />
              <Text
                style={[
                  styles.genderText,
                  form.gender === label && styles.genderTextActive,
                ]}
              >
                {label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* ── Địa chỉ field ── */}
      <View style={styles.fieldRow}>
        <View style={styles.fieldLabel}>
          <Feather name="map-pin" size={15} color={TEAL} />
          <Text style={styles.labelText}>Địa chỉ</Text>
        </View>
        <TextInput
          style={[
            styles.input,
            !!fieldErrors.address && styles.inputError,
          ]}
          value={form.address}
          onChangeText={(v) => handleChange("address", v)}
          placeholder="Nhập địa chỉ"
          placeholderTextColor="#B0B8C1"
        />
        {!!fieldErrors.address && (
          <Text style={styles.errorText}>{fieldErrors.address}</Text>
        )}
      </View>

      {/* Save button */}
      <TouchableOpacity
        style={[styles.saveBtn, isSaving && styles.saveBtnDisabled]}
        onPress={handleSave}
        disabled={isSaving}
      >
        {isSaving ? (
          <ActivityIndicator color="#FFFFFF" />
        ) : (
          <Text style={styles.saveBtnText}>Lưu thay đổi</Text>
        )}
      </TouchableOpacity>

      {/* Calendar modal */}
      <CalendarPicker
        visible={showCalendar}
        initialDate={form.birthDate}
        onSelect={(dateStr) => handleChange("birthDate", dateStr)}
        onClose={() => setShowCalendar(false)}
      />
    </View>
  );
}

// ── Styles ───────────────────────────────────────────────
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
    borderColor: TEAL,
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 14,
    color: "#1A1A1A",
    backgroundColor: "#FFFFFF",
    marginBottom: 4,
  },
  inputError: {
    borderColor: "#EF4444",
  },
  errorText: {
    fontSize: 12,
    color: "#EF4444",
    marginBottom: 4,
    paddingLeft: 2,
  },

  // ── Date row (input + calendar button) ──
  dateRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  calendarBtn: {
    width: 40,
    height: 40,
    borderRadius: 8,
    backgroundColor: TEAL,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 4,
  },

  // ── Gender picker ──
  genderRow: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 6,
  },
  genderOption: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: "#D1D5DB",
    backgroundColor: "#FFFFFF",
  },
  genderOptionActive: {
    borderColor: TEAL,
    backgroundColor: "#E8F8F4",
  },
  radioOuter: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: "#D1D5DB",
    alignItems: "center",
    justifyContent: "center",
  },
  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: TEAL,
  },
  genderText: {
    fontSize: 14,
    fontWeight: "500",
    color: "#6B7280",
  },
  genderTextActive: {
    color: TEAL,
    fontWeight: "600",
  },

  saveBtn: {
    margin: 16,
    backgroundColor: TEAL,
    borderRadius: 50,
    height: 48,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: TEAL,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  saveBtnDisabled: {
    opacity: 0.7,
  },
  saveBtnText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
});

// ── Calendar Styles ──────────────────────────────────────
const calStyles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.45)",
    justifyContent: "center",
    alignItems: "center",
  },
  container: {
    width: 320,
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 20,
    elevation: 10,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  navBtn: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1A1A1A",
  },
  weekRow: {
    flexDirection: "row",
    marginBottom: 4,
  },
  weekLabel: {
    flex: 1,
    textAlign: "center",
    fontSize: 12,
    fontWeight: "600",
    color: "#9CA3AF",
  },
  dayGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
  },
  dayCell: {
    width: "14.28%",
    aspectRatio: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  dayCellSelected: {
    backgroundColor: TEAL,
    borderRadius: 20,
  },
  dayText: {
    fontSize: 14,
    color: "#1A1A1A",
  },
  dayTextDisabled: {
    color: "#D1D5DB",
  },
  dayTextSelected: {
    color: "#FFFFFF",
    fontWeight: "700",
  },

  // Year picker
  yearGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 8,
  },
  yearBtn: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
    backgroundColor: "#F3F4F6",
  },
  yearBtnActive: {
    backgroundColor: TEAL,
  },
  yearText: {
    fontSize: 14,
    color: "#1A1A1A",
    fontWeight: "500",
  },
  yearTextActive: {
    color: "#FFFFFF",
    fontWeight: "700",
  },

  // Actions
  actions: {
    flexDirection: "row",
    justifyContent: "flex-end",
    gap: 10,
    marginTop: 12,
  },
  cancelBtn: {
    paddingVertical: 8,
    paddingHorizontal: 18,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D1D5DB",
  },
  cancelText: {
    fontSize: 14,
    color: "#6B7280",
    fontWeight: "500",
  },
  confirmBtn: {
    paddingVertical: 8,
    paddingHorizontal: 18,
    borderRadius: 8,
    backgroundColor: TEAL,
  },
  confirmText: {
    fontSize: 14,
    color: "#FFFFFF",
    fontWeight: "600",
  },
});
