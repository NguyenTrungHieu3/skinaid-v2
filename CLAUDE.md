# SkinAid — CLAUDE.md (Permanent Memory Layer)

> **Read this file first at the start of every session.**
> It is the single source of truth for architecture, APIs, patterns, and conventions.
> Do NOT re-scan source files unless debugging a specific issue — this file already captures everything.

---

## 1. Project Identity

| Field | Value |
|---|---|
| App name | **SkinAid** |
| Bundle ID | `com.skinaid.app` |
| Expo slug | `skinaid` |
| Version | 1.0.0 |
| Framework | Expo SDK (React Native) with **Expo Router** (file-based routing) |
| Language | TypeScript |
| Architecture | New Architecture enabled (`newArchEnabled: true`); React Compiler **disabled** (`reactCompiler: false`) |
| Orientation | Portrait-locked |

---

## 2. Tech Stack

### Core
- **React Native** + **Expo** (managed workflow, no bare ejection yet)
- **Expo Router v3+** — file-based navigation (`app/` directory)
- **TypeScript** (strict mode implied)

### Key Dependencies (from package.json)
| Package | Purpose |
|---|---|
| `expo-router` | File-based navigation |
| `axios` | HTTP client (centralised in `api/axiosClient.ts`) |
| `expo-secure-store` | Encrypted token storage |
| `expo-camera` | Camera feed for wound scanning |
| `expo-image-picker` | Photo library access for avatar upload |
| `expo-image-manipulator` | Image resizing/cropping/quality checks |
| `expo-linear-gradient` | Gradient UI elements |
| `expo-location` | GPS coordinates for map screen |
| `react-native-webview` | Renders Leaflet.js map in `facilities` screen |
| `@expo-google-fonts/inter` | Typography (Inter font family) |
| `@expo/vector-icons` | Icons (Feather, Ionicons) |
| `react-native-safe-area-context` | Safe area insets |
| `@react-native-masked-view/masked-view` | Gradient text in auth screens |

---

## 3. Directory Structure

```
myApp/
├── app/                        ← Expo Router pages (all screens)
│   ├── _layout.tsx             ← Root layout (AuthProvider + nav bar)
│   ├── (auth)/                 ← Auth group (no tab bar)
│   │   ├── sign-in.tsx
│   │   ├── sign-up.tsx
│   │   ├── forgot-password.tsx
│   │   └── change-password.tsx
│   ├── (tabs)/                 ← Main tabbed area
│   │   ├── _layout.tsx         ← Tab bar layout; exports useTabBarHeight()
│   │   ├── home.tsx
│   │   ├── history.tsx
│   │   ├── facilities.tsx
│   │   └── profile.tsx
│   ├── image-check.tsx         ← Image quality validation screen
│   ├── analyzing.tsx           ← AI analysis loading (4 s timer → result)
│   ├── analysis-result.tsx     ← Wound list + selection screen
│   ├── wound-assessment.tsx    ← Per-wound questionnaire screen
│   ├── assessment-loading.tsx  ← 3.8 s animated loader between quiz → result
│   ├── assessment-result.tsx   ← Final first-aid result screen
│   ├── history-detail.tsx      ← Detail + DermAid chat replay for a history entry
│   └── chat.tsx                ← Live DermAid chatbot screen
├── api/
│   └── axiosClient.ts          ← Axios singleton; Bearer token injection + 401 refresh
├── services/
│   ├── authService.ts          ← Auth API calls (sign-in, sign-up, profile, avatar, password)
│   ├── chatbotService.ts       ← Chatbot API (create session, send message, wound advisor)
│   ├── mapService.ts           ← Geoapify: nearby places, geocoding, routing, IP location
│   └── utils.ts                ← getErrorMessage() helper
├── context/
│   └── AuthContext.tsx         ← Global auth state; token, user, signIn, signOut
├── components/
│   ├── AuthComponents.tsx      ← AuthHeader, InputField, PrimaryButton, BackToLogin
│   ├── analysis/               ← AnalysisSummaryCard, WoundListItem, AnalyzingLoader
│   ├── image-check/            ← CheckTopBar, CropModal, FailState, ImagePreview, LoadingState, SuccessState
│   ├── map/                    ← FilterChips, MapWebView, PlaceCard, RouteStepsSheet
│   ├── profile/                ← PersonalInfoEdit, PersonalInfoView, ProfileHeader, ProfileTabs, SettingsView
│   └── scan/                   ← NoCameraPermission, ScanBottomBar, ScanFrame, ScanTopBar
├── constants/
│   ├── colors.ts               ← Colors object (single source of truth for all colours)
│   ├── analysisTypes.ts        ← TypeScript types for analysis results + MOCK_ANALYSIS_RESULT + MOCK_HISTORY_DETAILS
│   ├── imageCheckTypes.ts      ← CheckStatus type, ImageQualityIssue type
│   └── woundQuestions.ts       ← WOUND_QUESTION_SETS (questionnaire data for 6 wound types)
├── utils/
│   ├── imageQualityCheck.ts    ← checkImageQuality(), autoFixImage() using expo-image-manipulator
│   └── validation.ts           ← validateUsername(), validatePassword() form validation
└── assets/                     ← logo_1.png, logo_2.png, logo_DermAid.png, images/
```

---

## 4. Environment & Configuration

### API Server
```
Base URL: http://52.20.177.68/api/v1
```
Set in `api/axiosClient.ts` as `BASE_URL` constant.

### Third-Party Keys
| Service | Key |
|---|---|
| Geoapify (maps + geocoding + routing) | `e9e9f16da4f84d62983b6862a9399985` |

### Android-Specific
- `usesCleartextTraffic: true` — allows HTTP to the dev API server.
- `edgeToEdgeEnabled: true` — full-screen mode; handle insets manually everywhere.
- `predictiveBackGestureEnabled: false`.
- Permissions: CAMERA, RECORD_AUDIO, ACCESS_COARSE_LOCATION, ACCESS_FINE_LOCATION.

---

## 5. Authentication System

### AuthContext (`context/AuthContext.tsx`)
Wraps the entire app (mounted in `app/_layout.tsx`). Provides:
```ts
const { token, user, signIn, signOut, refreshToken } = useAuth();
```
- `signIn(credentials, rememberMe)` → calls `authService.signIn()`, stores tokens in `expo-secure-store`.
- `signOut()` → clears SecureStore + resets state.
- Auto-refresh: on mount, reads stored access token; if expired, calls refresh.
- Token keys in SecureStore: `"accessToken"`, `"refreshToken"`, `"rememberMe"`.

### Axios Client (`api/axiosClient.ts`)
- **Request interceptor**: attaches `Authorization: Bearer <token>` to every request.
- **Response interceptor**: on 401, calls `refreshToken()`, retries original request once; if still 401, calls `signOut()`.
- Timeout: none explicitly set (uses Axios default).

### Auth Routes
All under `app/(auth)/`:
- `sign-in.tsx` — username + password, "remember me" checkbox, forgot-password link.
- `sign-up.tsx` — registration.
- `forgot-password.tsx` — password reset flow.
- `change-password.tsx` — authenticated password change (accessible from Profile > Settings).

---

## 6. Navigation Architecture

### Route Groups
- `(auth)` — sign-in, sign-up, forgot-password, change-password. No tab bar.
- `(tabs)` — home, history, facilities, profile. Has tab bar.
- Root-level modal-style screens — image-check, analyzing, analysis-result, wound-assessment, assessment-loading, assessment-result, history-detail, chat.

### Tab Bar
Defined in `app/(tabs)/_layout.tsx`. Exports a context:
```ts
// Usage from any tab child:
const tabBarHeight = useTabBarHeight();
```
Use `tabBarHeight` in `paddingBottom` for scrollable content inside tabs.

### Typical Navigation Flows

**Wound Analysis Flow:**
```
(tabs)/home
  → scan (camera)
  → image-check          // quality gate
  → analyzing            // 4s timer (TODO: real API)
  → analysis-result      // select wounds
  → wound-assessment     // questionnaire
  → assessment-loading   // 3.8s animated loader
  → assessment-result    // first-aid instructions
  → chat (optional)      // ask DermAid
```

**History Flow:**
```
(tabs)/history
  → history-detail  (params: { analysisId: string })
```

**Auth Flow:**
```
(auth)/sign-in → (tabs)/home
(auth)/sign-in → (auth)/sign-up
(auth)/sign-in → (auth)/forgot-password
(tabs)/profile → (auth)/change-password
```

---

## 7. API Services

### `authService.ts`
All calls go through `axiosClient`.

| Method | Endpoint | Body/Params | Purpose |
|---|---|---|---|
| `signIn(creds)` | `POST /auth/login` | `{ user_name, password }` | Login |
| `signUp(data)` | `POST /auth/register` | `{ user_name, email, password, ... }` | Register |
| `getProfile()` | `GET /auth/profile` | — | Fetch logged-in user profile |
| `updateProfile(data)` | `PUT /auth/profile` | `{ full_name, phone, date_of_birth, gender, address }` | Update profile |
| `uploadAvatar(formData)` | `POST /auth/avatar` | multipart FormData with `file` field | Upload avatar |
| `changePassword(data)` | `POST /auth/change-password` | `{ old_password, new_password }` | Change password |
| `forgotPassword(email)` | `POST /auth/forgot-password` | `{ email }` | Send reset email |
| `resetPassword(data)` | `POST /auth/reset-password` | `{ token, new_password }` | Confirm reset |
| `refreshToken(token)` | `POST /auth/refresh` | `{ refresh_token }` | Refresh access token |

**Profile response shape (`data.data`):**
```ts
{
  full_name: string;
  phone: string;
  date_of_birth: string;    // ISO date string
  gender: string;
  gender_display: string;   // localised display value
  address: string;
  avatar_url: string | null;
  created_at: string;       // ISO datetime
}
```

### `chatbotService.ts`
Dual-mode chatbot:
- **App Guide mode** — session-based, stored in Redis (ephemeral). Used in `chat.tsx`.
- **Wound Advisor mode** — persistent sessions stored in PostgreSQL. Used in `assessment-result.tsx`.

| Method | Endpoint | Purpose |
|---|---|---|
| `createSession(chatHistoryId)` | `POST /chatbot/session` | Create App Guide session (pass `null` for fresh) |
| `sendMessage(sessionId, message)` | `POST /chatbot/message` | Send to App Guide, receive reply |
| `createWoundSession(data)` | `POST /chatbot/wound-session` | Create persistent Wound Advisor session |
| `sendWoundMessage(sessionId, message)` | `POST /chatbot/wound-message` | Send to Wound Advisor |

**Session creation request:**
```ts
{ chat_history_id: string | null }
```
**Session creation response:**
```ts
{ data: { session_id: string } }
```
**Send message response:**
```ts
{ data: { reply: string } }
```

**Session limit in App Guide:** `MAX_USER_MESSAGES = 10` per session (enforced client-side in `chat.tsx`).

### `mapService.ts`
All calls use Geoapify APIs. Key functions:

| Function | Description |
|---|---|
| `getNearbyPlaces({ latitude, longitude, radius, category })` | Geoapify Places API — returns `NearbyPlace[]` |
| `geocodeAddress(query)` | Geoapify Geocoding API — returns `{ latitude, longitude }` |
| `getRoute({ origin_lat, origin_lng, dest_lat, dest_lng, mode })` | Geoapify Routing API (mode: `"drive"`) — returns `RouteData` |
| `getLocationByIP()` | `ip-api.com` — fast location fallback before GPS |

**NearbyPlace shape:**
```ts
{
  place_id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  category: string;
  distance?: number;
}
```

**Filter categories** (defined in `components/map/FilterChips.tsx`):
- `nearest` → `healthcare`
- `hospital` → `healthcare.hospital`
- `pharmacy` → `commercial.health_and_beauty.pharmacy`
- `clinic` → `healthcare.clinic_or_praxis`

---

## 8. Constants & Design System

### Colors (`constants/colors.ts`)
**NEVER hardcode colours.** Always import from here:
```ts
import { Colors } from '../constants/colors';
```

Key tokens:
| Token | Value | Usage |
|---|---|---|
| `Colors.primary` | `#02A18D` | Brand teal — buttons, icons, accents |
| `Colors.primaryDark` | `#007A6B` | Darker teal — gradients, hover states |
| `Colors.primaryLight` | `#3DBFA0` | Lighter teal — gradient start |
| `Colors.primaryFocused` | `#027A6D` | Input focus border |
| `Colors.white` | `#FFFFFF` | Backgrounds, card surfaces |
| `Colors.background` | `#FFFFFF` | Page background |
| `Colors.backgroundSecondary` | `#F7F8FA` | Screen background |
| `Colors.backgroundTertiary` | `#EFF1F3` | Input backgrounds, disabled states |
| `Colors.textPrimary` | `#1A1A1A` | Main body text |
| `Colors.textLight` | `#6B7280` | Secondary text |
| `Colors.textMuted` | `#9CA3AF` | Placeholder, hints |
| `Colors.borderLight` | `#E5E7EB` | Card borders, dividers |
| `Colors.borderInput` | `#B0B8C1` | Input field border fallback |
| `Colors.shadow` | `#000000` | Shadow colour (use with opacity) |
| `Colors.gradientAppName` | `['#02A18D', '#006A5E']` | App name gradient |

---

## 9. Data Types & Mock Data

### `constants/analysisTypes.ts`
Central types for the analysis/history pipeline:

```ts
// Wound detected by AI from an image
interface DetectedWound {
  id: string;
  woundTypeId: string;       // e.g. 'bong', 'tray', 'bam', 'mun-trung-ca', 'vay-nen', 'nam-da'
  label: string;             // e.g. 'Bỏng'
  confidence: number;        // 0–100
  severity?: string;
  boundingBox: BoundingBox;  // { x, y, width, height } — normalised 0–1
  selected: boolean;         // user toggle
}

// AI result for a single analysis session
interface AnalysisResult {
  id: string;
  imageUri: string;
  timestamp: string;
  deviceModelAccuracy: number;
  wounds: DetectedWound[];
}

// Wound detail used in assessment-result + history-detail
interface WoundDetail {
  id: string;
  woundType: string;
  label: string;
  accuracy: number;
  hasSeverity: boolean;
  severity?: string;
  severityColor?: string;
  recoveryTime: string;
  boundingBox: BoundingBox;
  imageUri: string;
  firstAid: FirstAidSection[];
  userAnswers?: { questionText: string; selectedOptions: string[] }[];
}

interface FirstAidSection {
  title: 'Sơ cứu ngay' | 'Nên làm' | 'Không nên làm';
  icon: string;
  steps: { content: string }[];
}

// Chat history message stored in a history entry
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

// A full past analysis record (used in history-detail)
interface AnalysisHistoryDetail {
  id: string;
  date: string;
  imageUri?: string;
  wounds: WoundDetail[];
  chatHistory: ChatMessage[];
}
```

**Mock data exports:**
- `MOCK_ANALYSIS_RESULT: AnalysisResult` — used in `analysis-result.tsx` (TODO: replace with real API call in `analyzing.tsx`).
- `MOCK_HISTORY_DETAILS: AnalysisHistoryDetail[]` — used in `history-detail.tsx` (IDs: `h001`, `h002`, `h003`).

### `constants/woundQuestions.ts`
Questionnaire data for 6 wound types. Key exports:

```ts
const WOUND_QUESTION_SETS: WoundQuestionSet[]

// Helper — returns question sets for an array of wound type IDs
function getQuestionSetsForWounds(woundTypeIds: string[]): WoundQuestionSet[]
```

**Wound type IDs** (used throughout codebase):
| ID | Label |
|---|---|
| `bong` | Bỏng (burn) |
| `tray` | Trầy xước (abrasion) |
| `bam` | Bầm (bruise) |
| `mun-trung-ca` | Mụn trứng cá (acne) |
| `vay-nen` | Vảy nến (psoriasis) |
| `nam-da` | Nấm da (ringworm) |

---

## 10. Image Quality Check

File: `utils/imageQualityCheck.ts`

```ts
// Run all quality checks on an image
const result = await checkImageQuality(imageUri: string): Promise<{
  passed: boolean;
  issues: ImageQualityIssue[];
}>

// Auto-fix identified issues (rotate, resize, enhance contrast)
const { fixedUri } = await autoFixImage(imageUri: string, issues: ImageQualityIssue[]): Promise<{
  fixedUri: string;
}>
```

**Issue types** (`constants/imageCheckTypes.ts`):
- `"blur"` — image is too blurry
- `"too_small"` — resolution too low
- `"bad_aspect_ratio"` — image is too narrow or wide
- `"dark"` — image is underexposed

Uses `expo-image-manipulator` for resizing and compression. The check is client-side only — runs before the image is sent to any API.

**Screen flow:** `image-check.tsx` calls `checkImageQuality()` automatically on mount. On failure → shows `FailState.tsx` with "Auto Fix" and "Skip" options.

---

## 11. Screen-by-Screen Reference

### `(tabs)/home.tsx`
- Scan button → navigates to camera scan screen (not a separate route; inline modal or `ScanFrame` component).
- Likely uses `components/scan/` components.
- Quick links to history and facilities.

### `(tabs)/history.tsx`
- Shows `HISTORY_RECORDS` (static mock, 6 entries with time-based filter).
- Filter options: All / 1d / 3d / 7d / 1m (dropdown).
- Search: filters by wound title substring.
- Grouped by month dynamically.
- Card press → `router.push({ pathname: '/history-detail', params: { analysisId } })`.

### `(tabs)/facilities.tsx`
- Map rendered via **Leaflet.js in a WebView** (`components/map/MapWebView.tsx`).
- Location strategy: IP-based fast location first, then GPS precision.
- Search is a Modal (separate Android Window) to avoid WebView IME conflict.
- Route directions via Geoapify Routing API, rendered as polyline on map.
- Key state: `gpsCoords` (GPS only), `mapCenter` (GPS or search). Never mutate `gpsCoords` on search.

### `(tabs)/profile.tsx`
- Fetches profile from `authService.getProfile()` on mount and after token change.
- Two tabs: **Thông tin cá nhân** (view/edit) + **Cài đặt** (settings).
- Edit mode → `PersonalInfoEdit.tsx` (calls `authService.updateProfile()`).
- Avatar upload → `authService.uploadAvatar(formData)`.
- Logout → `signOut()` + `router.replace('/(auth)/sign-in')`.

### `image-check.tsx`
- Receives `uri` param.
- Runs `checkImageQuality()` automatically. States: `"loading"` / `"success"` / `"fail"`.
- Crop modal: `CropModal.tsx` (uses expo-image-manipulator).
- On success → `router.push({ pathname: '/analyzing', params: { uri } })`.

### `analyzing.tsx`
- **Simulated** 4-second timer, then navigates to `analysis-result`.
- **TODO (critical)**: Replace `setTimeout` with actual API call to the wound analysis endpoint.
- Shows `AnalyzingLoader` component.

### `analysis-result.tsx`
- Receives `uri` param.
- Currently uses `MOCK_ANALYSIS_RESULT` (will be replaced by real API response).
- User selects wounds to analyse further.
- Continue → `router.push({ pathname: '/wound-assessment', params: { woundTypeIds: JSON.stringify([...]), imageUri: uri } })`.

### `wound-assessment.tsx`
- Receives `woundTypeIds: string` (JSON array) + `imageUri`.
- Calls `getQuestionSetsForWounds(typeIds)` to build questionnaire.
- Progress bar tracks answered questions.
- Per-wound-type accent colours (`WOUND_ACCENT` map).
- On finish → `router.replace('/assessment-loading', ...)`.

### `assessment-loading.tsx`
- 3.8-second animated loader with progress bar and step text.
- Navigates to `assessment-result` passing same params.
- **TODO**: Integrate with backend API for real result generation.

### `assessment-result.tsx`
- Receives `woundTypeIds` + `imageUri`.
- Contains `WOUND_DETAILS_MAP` (static first-aid data for all 6 wound types).
- Medical disclaimer pulses at the top.
- Multi-wound tabs if multiple wounds selected.
- Bottom bar: "Hỏi DermAid" (→ `chat.tsx`) + "Về trang chủ".

### `history-detail.tsx`
- Receives `analysisId` param.
- Looks up `MOCK_HISTORY_DETAILS.find(d => d.id === analysisId)`.
- Two tabs: **Chi tiết phân tích** (wound detail) + **Tư vấn cùng DermAid** (read-only chat replay).
- Sub-tabs for multiple wounds within the detail tab.

### `chat.tsx`
- Creates a chatbot session on mount via `chatbotService.createSession(null)`.
- Max 10 user messages per session.
- Platform-specific keyboard handling: `KeyboardAvoidingView` on iOS, `Animated.View` on Android.
- Shows `SessionInitOverlay` while connecting, with retry option.
- Bot avatar: `assets/logo_DermAid.png`.

---

## 12. Reusable Components

### `components/AuthComponents.tsx`
Shared across all auth screens:
- `AuthHeader` — logo + gradient "SkinAid" text (uses `MaskedView`).
- `InputField` — styled input with left icon and optional right icon.
- `PrimaryButton` — teal rounded button.
- `BackToLogin` — navigation link back to sign-in.

**Exported constants**: `TEAL = Colors.primary`, `TEAL_DARK = Colors.primaryFocused`.

### `components/map/MapWebView.tsx`
- Uses `react-native-webview` to render Leaflet.js.
- Exposes `MapWebViewHandle` ref with imperative methods:
  - `flyTo(lat, lng, zoom)`
  - `setUserLocation(lat, lng)`
  - `setPlaces(places, selectedPlaceId)`
  - `setRoute(polyline: number[][])`
  - `clearRoute()`
  - `fitBounds(polyline: number[][])`
- Communicates back via `onMarkerPress(placeId)` and `onMapPress()` callbacks.

### `components/profile/PersonalInfoEdit.tsx`
- The most complex single component (~23KB).
- Form with all profile fields + date picker + gender selector.
- Calls `authService.updateProfile()` on save.

---

## 13. Utilities

### `utils/validation.ts`
```ts
validateUsername(value: string): string  // Returns error message or ""
validatePassword(value: string): string  // Returns error message or ""
```

### `services/utils.ts`
```ts
getErrorMessage(error: any): string  // Extracts human-readable error from axios errors
```

---

## 14. Known TODOs & Integration Points

> These are the primary gaps between current mock state and production:

1. **`analyzing.tsx`** — `setTimeout` fake analysis must be replaced with:
   ```ts
   const result = await analysisService.analyze(uri);
   // Then navigate with real result instead of MOCK_ANALYSIS_RESULT
   ```

2. **`analysis-result.tsx`** — Currently uses `MOCK_ANALYSIS_RESULT`. Needs to receive real `AnalysisResult` from the analysis API (pass via params or shared state).

3. **`wound-assessment.tsx`** — `handleFinish()` has `TODO: send answers to API`. Must POST answers and receive real severity/recommendation from backend.

4. **`assessment-loading.tsx`** — Must call the backend assessment API instead of just waiting.

5. **`history.tsx`** + **`history-detail.tsx`** — Static mock data (`HISTORY_RECORDS`, `MOCK_HISTORY_DETAILS`) must be replaced with API calls.

6. **`chat.tsx`** Google Sign-In button — UI exists but is not functional.

---

## 15. Common Patterns & Conventions

### Navigation
- Use `router.replace()` when navigating forward in a flow (prevents back-stacking loading screens).
- Use `router.push()` for detail screens where back navigation is expected.
- Use `router.back()` for cancel/close actions.
- Always pass params as strings or JSON strings (Expo Router serialises to URL).

### Safe Area
- Most screens use `useSafeAreaInsets()` directly on the root `View`:
  ```tsx
  <View style={[styles.root, { paddingTop: insets.top }]}>
  ```
- Tab screens use `SafeAreaView` from `react-native-safe-area-context`.

### Keyboard Handling
```tsx
// iOS:
<KeyboardAvoidingView behavior="padding" keyboardVerticalOffset={insets.top + 56}>

// Android:
const inputBarBottom = useRef(new Animated.Value(0)).current;
Keyboard.addListener('keyboardDidShow', (e) => {
  Animated.timing(inputBarBottom, { toValue: e.endCoordinates.height, ... }).start();
});
```

### StyleSheet Pattern
Always use `StyleSheet.create({})`. Never inline style objects on render (performance).

### API Error Handling
Always use `getErrorMessage(error)` from `services/utils.ts` when showing errors to users.

### Image Upload Pattern
```ts
const formData = new FormData();
formData.append('file', {
  uri: asset.uri,
  name: asset.fileName || `filename_${Date.now()}.jpg`,
  type: asset.mimeType || 'image/jpeg',
} as unknown as Blob);
await authService.uploadAvatar(formData);
```

### Animated Patterns
- All loading screens use `Animated.loop()` with `Animated.sequence()` for pulse/spin effects.
- Progress bars use `Animated.timing()` with `useNativeDriver: false` (layout animations).
- Entry animations use `Animated.timing()` from `opacity: 0` to `opacity: 1`.

---

## 16. App.json / Expo Config Highlights

- `newArchEnabled: true` — Fabric/JSI enabled.
- `reactCompiler: false` — React Compiler is explicitly OFF. Do NOT add `'use memo'` directives.
- `edgeToEdgeEnabled: true` — Android 15 edge-to-edge. Always handle insets.
- `usesCleartextTraffic: true` — HTTP to dev API allowed on Android.
- Scheme: `skinaid://` — deep linking enabled.
- Font plugin: `expo-font` — Inter fonts loaded via `@expo-google-fonts/inter`.

---

## 17. Assets

| File | Usage |
|---|---|
| `assets/logo_1.png` | App logo (teal icon, shown in profile + auth header) |
| `assets/logo_2.png` | App icon (used for Expo icon + adaptive icon) |
| `assets/logo_DermAid.png` | DermAid chatbot avatar (chat screen + history detail) |
| `assets/images/favicon.png` | Web favicon |

---

*Last updated: comprehensive audit of full codebase including all screens, services, components, constants, and utilities.*
