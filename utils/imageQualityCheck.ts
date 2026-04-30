// utils/imageQualityCheck.ts
// Kiểm tra chất lượng ảnh phía client — không cần server/API
// SDK 54: expo-file-system (File class) + expo-image-manipulator (imperative API)

// ✅ expo-file-system new API — dùng File class, không dùng getInfoAsync
import { File } from "expo-file-system";
// ✅ expo-image-manipulator new API — dùng ImageManipulator.manipulate() static method
//    Hoạt động trong utility function (không phải hook), không bị deprecated
import { ImageManipulator, SaveFormat } from "expo-image-manipulator";
import { Image } from "react-native";
import {
  QUALITY_ISSUES,
  type ImageQualityIssue,
} from "../constants/imageCheckTypes";

// ── Ngưỡng chất lượng ─────────────────────────────────────────────
const MIN_DIMENSION = 300;    // px — chiều nhỏ nhất chấp nhận
const MIN_FILE_SIZE = 20;     // KB  — ảnh < 20KB thường quá nén/nhỏ
const MAX_FILE_SIZE = 20480;  // KB  — ảnh > 20MB là quá lớn
const MAX_ASPECT_RATIO = 4.0; // Tỉ lệ chiều w:h hoặc h:w tối đa

// ── Helper: lấy kích thước ảnh ────────────────────────────────────
function getImageDimensions(uri: string): Promise<{ w: number; h: number }> {
  return new Promise((resolve, reject) => {
    Image.getSize(
      uri,
      (w, h) => resolve({ w, h }),
      (error) => reject(error)
    );
  });
}

// ── Helper: lấy kích thước file (KB) ──────────────────────────────
// ✅ MIGRATED: FileSystem.getInfoAsync → File.size (new SDK 54 API, synchronous)
async function getFileSizeKB(uri: string): Promise<number | null> {
  try {
    const file = new File(uri);
    if (!file.exists) return null;
    const sizeBytes = file.size;
    return typeof sizeBytes === "number" ? sizeBytes / 1024 : null;
  } catch {
    return null;
  }
}

// ── Helper: thực hiện thao tác ảnh dùng new imperative API ────────
// ✅ MIGRATED: manipulateAsync → ImageManipulator.manipulate() chain API
async function applyManipulation(
  uri: string,
  transform: {
    resize?: { width: number; height: number };
    crop?: { originX: number; originY: number; width: number; height: number };
  },
  saveOpts: { compress: number; format: SaveFormat }
): Promise<string> {
  const ctx = ImageManipulator.manipulate(uri);
  if (transform.resize) ctx.resize(transform.resize);
  if (transform.crop)   ctx.crop(transform.crop);
  const ref = await ctx.renderAsync();
  const result = await ref.saveAsync({ compress: saveOpts.compress, format: saveOpts.format });
  return result.uri;
}

// ── Kiểm tra chất lượng ảnh ───────────────────────────────────────
export async function checkImageQuality(uri: string): Promise<{
  passed: boolean;
  issues: ImageQualityIssue[];
}> {
  const issues: ImageQualityIssue[] = [];

  // ── Check 1: Kích thước tối thiểu & Aspect ratio ──────────────
  try {
    const { w, h } = await getImageDimensions(uri);

    if (w < MIN_DIMENSION || h < MIN_DIMENSION) {
      issues.push(QUALITY_ISSUES.size);
    }

    const ratio = Math.max(w / h, h / w);
    if (ratio > MAX_ASPECT_RATIO) {
      issues.push(QUALITY_ISSUES.aspect);
    }
  } catch {
    issues.push(QUALITY_ISSUES.unclear);
  }

  // ── Check 2: Kích thước file ──────────────────────────────────
  const sizeKB = await getFileSizeKB(uri);
  if (sizeKB !== null) {
    if (sizeKB < MIN_FILE_SIZE) {
      issues.push(QUALITY_ISSUES.tooSmall);
    } else if (sizeKB > MAX_FILE_SIZE) {
      issues.push(QUALITY_ISSUES.tooLarge);
    }
  }

  // ── Check 3: Heuristic blur detection ────────────────────────
  // Kỹ thuật: resize ảnh về 2 size khác nhau rồi so sánh file size
  // Ảnh sắc nét → nhiều chi tiết → nén kém hơn ảnh mờ
  try {
    if (await detectBlurHeuristic(uri)) {
      issues.push(QUALITY_ISSUES.blur);
    }
  } catch {
    // Bỏ qua nếu không check được
  }

  return { passed: issues.length === 0, issues };
}

// ── Heuristic blur detection ──────────────────────────────────────
async function detectBlurHeuristic(uri: string): Promise<boolean> {
  try {
    const largeUri = await applyManipulation(
      uri,
      { resize: { width: 200, height: 200 } },
      { compress: 0.9, format: SaveFormat.JPEG }
    );
    const smallUri = await applyManipulation(
      uri,
      { resize: { width: 50, height: 50 } },
      { compress: 0.9, format: SaveFormat.JPEG }
    );

    const sizeL = await getFileSizeKB(largeUri);
    const sizeS = await getFileSizeKB(smallUri);

    if (sizeL === null || sizeS === null || sizeS === 0) return false;

    // Ảnh sắc nét: ratio > 4; Ảnh mờ: ratio < 2.5
    return sizeL / sizeS < 2.5;
  } catch {
    return false;
  }
}

// ── Auto-fix ảnh theo danh sách issues ───────────────────────────
export async function autoFixImage(
  uri: string,
  issues: ImageQualityIssue[]
): Promise<{ fixedUri: string; fixedIssues: string[] }> {
  const issueIds = issues.map((i) => i.id);
  const fixedIssues: string[] = [];
  let currentUri = uri;

  // Fix 1: Ảnh quá lớn → nén lại
  if (issueIds.includes("tooLarge")) {
    try {
      currentUri = await applyManipulation(
        currentUri,
        {},
        { compress: 0.65, format: SaveFormat.JPEG }
      );
      fixedIssues.push("tooLarge");
    } catch {}
  }

  // Fix 2: Kích thước quá nhỏ → upscale (tối đa 2×)
  if (issueIds.includes("size")) {
    try {
      const { w, h } = await getImageDimensions(currentUri);
      if (w < MIN_DIMENSION || h < MIN_DIMENSION) {
        const scale = Math.min(2.0, MIN_DIMENSION / Math.min(w, h));
        currentUri = await applyManipulation(
          currentUri,
          { resize: { width: Math.round(w * scale), height: Math.round(h * scale) } },
          { compress: 0.9, format: SaveFormat.JPEG }
        );
        fixedIssues.push("size");
      }
    } catch {}
  }

  // Fix 3: Tỉ lệ bất thường → crop về center với tỉ lệ 4:3
  if (issueIds.includes("aspect")) {
    try {
      const { w, h } = await getImageDimensions(currentUri);
      const targetRatio = 4 / 3;
      let cropW: number, cropH: number, originX: number, originY: number;

      if (w / h > targetRatio) {
        cropH = h;
        cropW = Math.round(h * targetRatio);
        originX = Math.round((w - cropW) / 2);
        originY = 0;
      } else {
        cropW = w;
        cropH = Math.round(w / targetRatio);
        originX = 0;
        originY = Math.round((h - cropH) / 2);
      }

      currentUri = await applyManipulation(
        currentUri,
        { crop: { originX, originY, width: cropW, height: cropH } },
        { compress: 0.9, format: SaveFormat.JPEG }
      );
      fixedIssues.push("aspect");
    } catch {}
  }

  // Fix 4: Ảnh mờ → tăng chất lượng JPEG để giảm nén artifact
  if (issueIds.includes("blur")) {
    try {
      currentUri = await applyManipulation(
        currentUri,
        {},
        { compress: 1.0, format: SaveFormat.JPEG }
      );
      fixedIssues.push("blur");
    } catch {}
  }

  return { fixedUri: currentUri, fixedIssues };
}
