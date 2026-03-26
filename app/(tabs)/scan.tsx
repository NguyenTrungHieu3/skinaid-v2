// app/(tabs)/scan.tsx
import { StyleSheet, Text, View } from "react-native";
export default function ScanScreen() {
  return (
    <View style={styles.center}>
      <Text style={styles.text}>📷 Scan</Text>
      <Text style={styles.sub}>Camera scan coming soon...</Text>
    </View>
  );
}
const styles = StyleSheet.create({
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#fff",
  },
  text: { fontSize: 20, fontWeight: "700", color: "#1A1A1A" },
  sub: { fontSize: 14, color: "#9CA3AF", marginTop: 8 },
});
