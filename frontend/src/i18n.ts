// src/i18n.ts
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import enTranslations from "./locales/en.json";
import viTranslations from "./locales/vi.json";

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: enTranslations },
      vi: { translation: viTranslations },
    },

    // 1. Đặt ngôn ngữ mặc định là Tiếng Việt
    // (Nó sẽ được dùng khi không tìm thấy ngôn ngữ nào trong bộ nhớ)
    fallbackLng: "vi",

    detection: {
      // 2. QUAN TRỌNG: Chỉ tìm trong localStorage (hoặc cookie)
      // Xóa "navigator" để bỏ qua việc phát hiện ngôn ngữ trình duyệt (tránh trường hợp trình duyệt tiếng Anh tự nhảy sang EN)
      order: ["localStorage", "cookie"],

      // Nơi lưu trữ ngôn ngữ khi người dùng chủ động bấm đổi
      caches: ["localStorage"],
    },

    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
