import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import enTranslations from "./locales/en.json";
import viTranslations from "./locales/vi.json";

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: enTranslations },
    vi: { translation: viTranslations },
  },
  lng: "vi", // Ngôn ngữ mặc định
  fallbackLng: "en", // Ngôn ngữ dự phòng
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
