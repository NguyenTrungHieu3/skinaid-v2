/**
 * facilities.tsx — Medical Facilities Map Screen
 * Uses Leaflet.js + Geoapify tiles (via MapWebView) — no Google Maps needed.
 */

import { Feather } from "@expo/vector-icons";
import * as Location from "expo-location";
import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  ActivityIndicator,
  Alert,
  Dimensions,
  Keyboard,
  Modal,
  Platform,
  Pressable,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import FilterChips, {
  FILTER_OPTIONS,
  FilterKey,
} from "../../components/map/FilterChips";
import MapWebView, {
  MapWebViewHandle,
} from "../../components/map/MapWebView";
import PlaceCard from "../../components/map/PlaceCard";
import RouteStepsSheet from "../../components/map/RouteStepsSheet";
import {
  geocodeAddress,
  getLocationByIP,
  getNearbyPlaces,
  getRoute,
  NearbyPlace,
  RouteData,
} from "../../services/mapService";

// ─── Types ───────────────────────────────────
interface Coords {
  latitude: number;
  longitude: number;
}

const DEFAULT_COORDS: Coords = { latitude: 21.0285, longitude: 105.8542 };
const MAP_HEIGHT = Math.round(Dimensions.get("window").height * 0.52);

export default function FacilitiesScreen() {
  // NOTE: React Compiler disabled globally in app.json → no 'use no memo' needed
  const insets = useSafeAreaInsets();
  const mapRef = useRef<MapWebViewHandle>(null);
  // Uncontrolled TextInput ref — fixes Android bug where
  // controlled value prop blocks native text rendering
  const searchInputRef = useRef<TextInput>(null);

  // GPS thực của user — KHÔNG thay đổi khi search địa chỉ
  const [gpsCoords,  setGpsCoords]  = useState<Coords>(DEFAULT_COORDS);
  // Tâm bản đồ / vùng search — thay đổi cả khi GPS lẫn khi search địa chỉ
  const [mapCenter,  setMapCenter]  = useState<Coords>(DEFAULT_COORDS);
  const [locationReady, setLocationReady] = useState(false);

  // Places
  const [places, setPlaces] = useState<NearbyPlace[]>([]);
  const [loadingPlaces, setLoadingPlaces] = useState(false);

  // Filter
  const [activeFilter, setActiveFilter] = useState<FilterKey>("nearest");

  // Selected + Route
  const [selectedPlace, setSelectedPlace] = useState<NearbyPlace | null>(null);
  const [routeData, setRouteData] = useState<RouteData | null>(null);
  const [routePolyline, setRoutePolyline] = useState<number[][]>([]);
  const [loadingRoute, setLoadingRoute] = useState(false);
  const [showSteps, setShowSteps] = useState(false);

  // Search
  const [searchText, setSearchText] = useState("");
  const [showSearch, setShowSearch] = useState(false); // Modal search
  const [loadingSearch, setLoadingSearch] = useState(false);

  // ── Sync GPS thực → WebView (chấm xanh trên bản đồ) ─────────────────────
  useEffect(() => {
    mapRef.current?.setUserLocation(gpsCoords.latitude, gpsCoords.longitude);
  }, [gpsCoords]);

  // ── Sync places + selectedPlace → WebView markers ──────────────────────
  useEffect(() => {
    mapRef.current?.setPlaces(places, selectedPlace?.place_id ?? null);
  }, [places, selectedPlace]);

  // ── Sync routePolyline → WebView route ─────────────────────────────────
  useEffect(() => {
    if (routePolyline.length > 0) {
      mapRef.current?.setRoute(routePolyline);
    } else {
      mapRef.current?.clearRoute();
    }
  }, [routePolyline]);

  // ── GPS location ───────────────────────────────────────────────────────
  const fetchGPS = useCallback(async (): Promise<Coords | null> => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") return null;
      const loc = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      const coords: Coords = {
        latitude: loc.coords.latitude,
        longitude: loc.coords.longitude,
      };
      setGpsCoords(coords);
      setMapCenter(coords);   // khi GPS cập nhật, map center cũng đi theo
      return coords;
    } catch {
      return null;
    }
  }, []);

  // ── Initial load: IP location → GPS ────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    (async () => {
      // 1. Fast: IP location
      try {
        const ip = await getLocationByIP();
        if (!cancelled && ip.latitude && ip.longitude) {
          const c: Coords = { latitude: ip.latitude, longitude: ip.longitude };
          setGpsCoords(c);
          setMapCenter(c);
          setLocationReady(true);
          mapRef.current?.flyTo(ip.latitude, ip.longitude, 14);
        }
      } catch {
        if (!cancelled) setLocationReady(true);
      }
      // 2. Accurate: GPS
      if (!cancelled) {
        const gps = await fetchGPS();
        if (gps && !cancelled) {
          setLocationReady(true);
          mapRef.current?.flyTo(gps.latitude, gps.longitude, 14);
        }
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // ── Fetch nearby places ─────────────────────────────────────────────────
  const fetchNearby = useCallback(
    async (coords: Coords, filter: FilterKey) => {
      const opt = FILTER_OPTIONS.find((o) => o.key === filter);
      if (!opt) return;
      setLoadingPlaces(true);
      try {
        const res = await getNearbyPlaces({
          latitude: coords.latitude,
          longitude: coords.longitude,
          radius: 5000,
          category: opt.apiCategory,
        });
        setPlaces(res ?? []);
      } catch (e: any) {
        console.warn("[Map] nearby-places:", e?.message);
        setPlaces([]);
      } finally {
        setLoadingPlaces(false);
      }
    },
    []
  );

  useEffect(() => {
    // Chỉ auto-fetch khi lần đầu locationReady và filter đổi
    // mapCenter thay đổi do search sẽ gọi fetchNearby directly, không qua effect
    if (locationReady) fetchNearby(mapCenter, activeFilter);
  }, [locationReady, activeFilter]); // xóa mapCenter khỏi deps → chỉ chạy khi filter/ready

  // ── Filter change ───────────────────────────────────────────────────────
  const handleFilterChange = useCallback(
    (key: FilterKey, _cat: string) => {
      setActiveFilter(key);
      setSelectedPlace(null);
      setRoutePolyline([]);
      setRouteData(null);
    },
    []
  );

  // ── Marker press (from WebView) ─────────────────────────────────────────
  const handleMarkerPress = useCallback(
    (placeId: string) => {
      const place = places.find((p) => p.place_id === placeId);
      if (!place) return;
      // Xóa route cũ khi chọn cơ sở mới
      setRoutePolyline([]);
      setRouteData(null);
      mapRef.current?.clearRoute();
      setSelectedPlace(place);
      mapRef.current?.flyTo(place.latitude - 0.004, place.longitude, 15);
    },
    [places]
  );

  // ── Map background tap: chỉ ẩn card, KHÔNG xóa route ────────────────
  const handleMapPress = useCallback(() => {
    if (selectedPlace) {
      setSelectedPlace(null);
      // Route vẫn giữ nguyên trên map
    }
  }, [selectedPlace]);

  // ── Dismiss card (bấm X hoặc swipe): chỉ ẩn card, KHÔNG xóa route ────
  const handleDismiss = useCallback(() => {
    setSelectedPlace(null);
    // Route vẫn hiển thị — người dùng có thể nhìn theo đường chỉ
  }, []);

  // ── Xóa route hoàn toàn (khi đổi filter / chọn cơ sở mới) ────────────
  const clearActiveRoute = useCallback(() => {
    setRoutePolyline([]);
    setRouteData(null);
    mapRef.current?.clearRoute();
  }, []);


  // ── Get directions ──────────────────────────────────────────────────────
  const handleGetDirections = useCallback(async () => {
    if (!selectedPlace) return;
    setLoadingRoute(true);
    try {
      const route = await getRoute({
        origin_lat: gpsCoords.latitude,
        origin_lng: gpsCoords.longitude,
        dest_lat: selectedPlace.latitude,
        dest_lng: selectedPlace.longitude,
        mode: "drive",   // Geoapify: "drive" not "driving"
      });
      setRouteData(route);
      if (route.geometry?.length > 0) {
        setRoutePolyline(route.geometry);
        mapRef.current?.fitBounds(route.geometry);
      }
      setShowSteps(true);
    } catch (e: any) {
      Alert.alert("Không tìm được đường", e?.message ?? "Lỗi không xác định");
    } finally {
      setLoadingRoute(false);
    }
  }, [selectedPlace, gpsCoords]);  // luôn dùng GPS thực

  // ── Search submit ───────────────────────────────────────────────────────
  const handleSearchSubmit = useCallback(async () => {
    const q = searchText.trim();
    if (!q) return;
    Keyboard.dismiss();
    setLoadingSearch(true);
    try {
      const res = await geocodeAddress(q);
      const c: Coords = { latitude: res.latitude, longitude: res.longitude };
      // Chỉ cập nhật mapCenter (địa chỉ search), KHÔNG đụng tới gpsCoords
      setMapCenter(c);
      mapRef.current?.flyTo(res.latitude, res.longitude, 14);
      // Load places quanh địa chỉ mới
      fetchNearby(c, activeFilter);
    } catch {
      Alert.alert("Không tìm thấy", `Không tìm thấy địa chỉ: "${q}"`);
    } finally {
      setLoadingSearch(false);
    }
  }, [searchText, activeFilter, fetchNearby]);

  // ── Recenter ─────────────────────────────────────────────────────────────
  const handleRecenter = useCallback(async () => {
    const gps = await fetchGPS();
    const c = gps ?? gpsCoords;
    setMapCenter(c);
    mapRef.current?.flyTo(c.latitude, c.longitude, 15);
    if (gps) fetchNearby(gps, activeFilter);
  }, [gpsCoords, activeFilter, fetchNearby]);

  // ── Search input handler (uncontrolled) ──────────────────────────
  // state chỉ dùng để render nút X; text hiển thị do native TextInput quản lý
  const handleChangeText = useCallback((text: string) => {
    setSearchText(text);
  }, []);

  // Xóa nội dung: dùng ref.clear() để xóa native + reset state
  const handleClearSearch = useCallback(() => {
    searchInputRef.current?.clear();
    setSearchText("");
  }, []);
  // ─────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────
  return (
    <View style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />

      {/* ── HEADER ── */}
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Text style={styles.headerTitle}>Cơ sở y tế</Text>
        {/* <Pressable
          style={styles.headerBtn}
          onPress={handleRecenter}
          accessibilityLabel="Vị trí của tôi"
        >
          <Feather name="crosshair" size={20} color="#374151" />
        </Pressable> */}
      </View>

      {/* ── SEARCH BAR (Pressable trigger → opens Modal) ── */}
      {/* NOTE: TextInput is inside a Modal to prevent Android WebView IME focus stealing.
          When WebView and TextInput are in the same Android Window, WebView can steal
          the IME (keyboard) connection, causing keys not to register in the TextInput.
          Modal renders in a separate Window layer → 100% keyboard goes to TextInput. */}
      <TouchableOpacity
        style={styles.searchWrap}
        activeOpacity={0.8}
        onPress={() => setShowSearch(true)}
        accessibilityLabel="Mở tìm kiếm cơ sở y tế"
      >
        <View style={[styles.searchBar, searchText.length > 0 && styles.searchBarFocused]}>
          <Feather name="search" size={17} color={searchText ? "#3DBFA0" : "#9CA3AF"} style={{ marginRight: 9 }} />
          <Text
            style={searchText ? styles.searchTextDisplay : styles.searchPlaceholder}
            numberOfLines={1}
          >
            {searchText || "Tìm kiếm phòng khám, bệnh viện..."}
          </Text>
          {searchText.length > 0 ? (
            <Pressable
              onPress={(e) => { e.stopPropagation?.(); setSearchText(""); }}
              hitSlop={8}
            >
              <Feather name="x-circle" size={17} color="#9CA3AF" />
            </Pressable>
          ) : (
            <View style={styles.sliderBtn}>
              <Feather name="sliders" size={15} color="#6B7280" />
            </View>
          )}
        </View>
      </TouchableOpacity>

      {/* ── SEARCH MODAL (separate Window → no WebView IME conflict) ── */}
      <Modal
        visible={showSearch}
        animationType="fade"
        transparent={false}
        statusBarTranslucent
        onRequestClose={() => setShowSearch(false)}
      >
        <View style={[styles.searchModalRoot, { paddingTop: insets.top }]}>
          <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />

          {/* Modal header */}
          <View style={styles.searchModalHeader}>
            <TouchableOpacity
              onPress={() => setShowSearch(false)}
              style={styles.searchModalBack}
              hitSlop={8}
            >
              <Feather name="arrow-left" size={22} color="#374151" />
            </TouchableOpacity>

            <View style={styles.searchModalBar}>
              <Feather name="search" size={16} color="#3DBFA0" style={{ marginRight: 8 }} />
              <TextInput
                style={styles.searchModalInput}
                placeholder="Tìm kiếm phòng khám, bệnh viện..."
                placeholderTextColor="#9CA3AF"
                value={searchText}
                onChangeText={setSearchText}
                autoFocus
                returnKeyType="search"
                autoCorrect={false}
                autoCapitalize="none"
                onSubmitEditing={() => {
                  handleSearchSubmit();
                  setShowSearch(false);
                }}
              />
              {loadingSearch ? (
                <ActivityIndicator size="small" color="#3DBFA0" />
              ) : searchText.length > 0 ? (
                <Pressable onPress={() => setSearchText("")} hitSlop={8}>
                  <Feather name="x-circle" size={17} color="#9CA3AF" />
                </Pressable>
              ) : null}
            </View>
          </View>

          {/* Gợi ý / instruction */}
          <View style={styles.searchModalHint}>
            <Feather name="map-pin" size={16} color="#9CA3AF" style={{ marginRight: 8 }} />
            <Text style={styles.searchModalHintText}>
              Nhập tên địa chỉ hoặc khu vực để tìm cơ sở y tế gần đó
            </Text>
          </View>
        </View>
      </Modal>

      {/* ── FILTER CHIPS ── */}
      <View style={styles.filterWrap}>
        <FilterChips selected={activeFilter} onChange={handleFilterChange} />
      </View>

      {/* ── MAP (WebView + Leaflet) ── */}
      <View style={styles.mapWrap}>
        <View style={{ flex: 1 }}>
          <MapWebView
            ref={mapRef}
            onMarkerPress={handleMarkerPress}
            onMapPress={handleMapPress}
          />
        </View>

        {/* Loading badge */}
        {loadingPlaces && (
          <View style={styles.loadingBadge}>
            <ActivityIndicator size="small" color="#3DBFA0" />
            <Text style={styles.loadingText}>Đang tải...</Text>
          </View>
        )}

        {/* Count badge */}
        {!loadingPlaces && places.length > 0 && (
          <View style={styles.countBadge}>
            <Feather name="map-pin" size={12} color="#fff" />
            <Text style={styles.countText}>{places.length} cơ sở</Text>
          </View>
        )}

        {/* Recenter FAB */}
        <Pressable
          style={styles.fab}
          onPress={handleRecenter}
          accessibilityLabel="Quay về vị trí của tôi"
        >
          <Feather name="navigation" size={18} color="#3DBFA0" />
        </Pressable>
      </View>

      {/* Empty state: chỉ log warn, không render block che map */}

      {/* ── PLACE CARD ── */}
      <PlaceCard
        place={selectedPlace}
        isLoadingRoute={loadingRoute}
        onGetDirections={handleGetDirections}
        onDismiss={handleDismiss}
      />

      {/* ── ROUTE STEPS ── */}
      <RouteStepsSheet
        visible={showSteps}
        routeData={routeData}
        destinationName={selectedPlace?.name ?? ""}
        onClose={() => setShowSteps(false)}
      />
    </View>
  );
}

// ─────────────────────────────────────────────
const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#F8FAFC" },

  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    paddingBottom: 12,
    backgroundColor: "#FFFFFF",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
    zIndex: 5,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: "800",
    color: "#111827",
    letterSpacing: -0.4,
  },
  headerBtn: {
    width: 38, height: 38, borderRadius: 12,
    backgroundColor: "#F3F4F6",
    alignItems: "center", justifyContent: "center",
  },

  searchWrap: {
    // paddingHorizontal: 16,
    // paddingVertical: 10,
    // backgroundColor: "#FFFFFF",
    // zIndex: 4,
    // elevation: 3,   // Android: đảm bảo touch priority trên WebView

    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: "#FFFFFF",

    zIndex: 9999,     // 👈 tăng max
    elevation: 20,    // 👈 Android rất quan trọng
    position: "relative",
  },

  searchBar: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#F3F4F6",
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: Platform.OS === "ios" ? 11 : 8,
    borderWidth: 1.5,
    borderColor: "transparent",
  },
  searchBarFocused: {
    borderColor: "#3DBFA0",
    backgroundColor: "#FFFFFF",
    shadowColor: "#3DBFA0",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
    color: "#111827",
    fontWeight: "500",
    paddingVertical: 0,
  },
  sliderBtn: {
    width: 28, height: 28, borderRadius: 7,
    backgroundColor: "#E5E7EB",
    alignItems: "center", justifyContent: "center",
  },

  filterWrap: {
    backgroundColor: "#FFFFFF",
    zIndex: 3,
    elevation: 2,
  },

  mapWrap: {
    width: "100%",
    flex: 1,              // fill remaining space → không còn mảng xám
    position: "relative",
    // zIndex: 0,
    overflow: "hidden",
    pointerEvents: "box-none",
  },

  loadingBadge: {
    position: "absolute", top: 12, right: 12,
    flexDirection: "row", alignItems: "center", gap: 6,
    backgroundColor: "rgba(255,255,255,0.93)",
    borderRadius: 20, paddingHorizontal: 12, paddingVertical: 6,
    shadowColor: "#000", shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1, shadowRadius: 6, elevation: 4,
  },
  loadingText: { fontSize: 12, fontWeight: "600", color: "#374151" },

  countBadge: {
    position: "absolute", top: 12, left: 12,
    flexDirection: "row", alignItems: "center", gap: 5,
    backgroundColor: "rgba(61,191,160,0.92)",
    borderRadius: 20, paddingHorizontal: 12, paddingVertical: 6,
    shadowColor: "#3DBFA0", shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3, shadowRadius: 6, elevation: 4,
  },
  countText: { fontSize: 12, fontWeight: "700", color: "#FFFFFF" },

  fab: {
    position: "absolute", bottom: 16, right: 16,
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: "#FFFFFF",
    alignItems: "center", justifyContent: "center",
    shadowColor: "#000", shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15, shadowRadius: 8, elevation: 6,
  },

  empty: {
    flex: 1, alignItems: "center", justifyContent: "center",
    paddingHorizontal: 40, gap: 8,
  },
  emptyTitle: { fontSize: 16, fontWeight: "700", color: "#374151" },
  emptySub:  { fontSize: 13, color: "#9CA3AF", textAlign: "center", lineHeight: 18 },

  // ── Search trigger text styles ─────────────────────────────────────────
  searchTextDisplay: {
    flex: 1, fontSize: 14, fontWeight: "500", color: "#111827",
  },
  searchPlaceholder: {
    flex: 1, fontSize: 14, fontWeight: "400", color: "#9CA3AF",
  },

  // ── Search Modal styles ────────────────────────────────────────────────
  searchModalRoot: {
    flex: 1, backgroundColor: "#FFFFFF",
  },
  searchModalHeader: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
    backgroundColor: "#FFFFFF",
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
  },
  searchModalBack: {
    width: 40, height: 40, borderRadius: 12,
    alignItems: "center", justifyContent: "center",
    marginRight: 8,
  },
  searchModalBar: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#F3F4F6",
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: Platform.OS === "ios" ? 10 : 7,
    borderWidth: 1.5,
    borderColor: "#3DBFA0",
  },
  searchModalInput: {
    flex: 1,
    fontSize: 14,
    fontWeight: "500",
    color: "#111827",
    paddingVertical: 0,
  },
  searchModalHint: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingVertical: 20,
    marginTop: 8,
  },
  searchModalHintText: {
    flex: 1,
    fontSize: 13,
    color: "#9CA3AF",
    lineHeight: 18,
  },
});
