// import i18n from "i18next";
// import { initReactI18next } from "react-i18next";
// import enTranslations from "./locales/en.json";
// import viTranslations from "./locales/vi.json";

// i18n.use(initReactI18next).init({
//   resources: {
//     en: { translation: enTranslations },
//     vi: { translation: viTranslations },
//   },
//   lng: "vi", // Ngôn ngữ mặc định
//   fallbackLng: "en", // Ngôn ngữ dự phòng
//   interpolation: {
//     escapeValue: false,
//   },
// });

// export default i18n;

// src/i18n.ts
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector"; // <--- 1. Import cái này

// Import các file dịch của bạn
import enTranslations from "./locales/en.json";
import viTranslations from "./locales/vi.json";

i18n
  .use(LanguageDetector) // <--- 2. Sử dụng plugin phát hiện ngôn ngữ
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: enTranslations },
      vi: { translation: viTranslations },
    },

    // --- 3. CẤU HÌNH QUAN TRỌNG ---

    // lng: "vi",  <--- XÓA HOẶC COMMENT DÒNG NÀY ĐI (Nếu để, nó sẽ ghi đè việc phát hiện ngôn ngữ)

    fallbackLng: "vi", // Ngôn ngữ dự phòng nếu không tìm thấy trong localStorage

    detection: {
      // Thứ tự ưu tiên để tìm ngôn ngữ:
      // 1. localStorage (lần trước đã chọn)
      // 2. cookie
      // 3. htmlTag
      // 4. navigator (ngôn ngữ trình duyệt)
      order: ["localStorage", "cookie", "navigator"],

      // Nơi lưu trữ ngôn ngữ khi người dùng thay đổi (cache lại)
      caches: ["localStorage"],
    },

    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
