import i18n from "i18next";

/**
 * Map common backend error codes / messages to i18n keys so the FE can
 * surface translated error banners regardless of the backend response
 * language. Used by the axios response interceptor (TC-CL-07).
 */
const ERROR_CODE_MAP: Record<string, string> = {
  AUTH_INVALID_CREDENTIALS: "errors.auth.invalid_credentials",
  AUTH_INVALID_RESET_TOKEN: "errors.auth.invalid_reset_token",
  AUTH_ACCOUNT_LOCKED: "errors.auth.account_locked",
  AUTH_ACCOUNT_DEACTIVATED: "errors.auth.account_deactivated",
  AUTH_WEAK_PASSWORD: "errors.auth.weak_password",
  AUTH_OLD_PASSWORD_INCORRECT: "errors.auth.old_password_incorrect",
  USER_NOT_FOUND: "errors.user.not_found",
  MAP_SERVICE_UNAVAILABLE: "errors.map.service_unavailable",
  LOCATION_NOT_FOUND: "errors.map.not_found",
  UPLOAD_INVALID_FILE: "errors.upload.invalid_file",
  UPLOAD_FILE_TOO_LARGE: "errors.upload.file_too_large",
  UPLOAD_DIMENSION_INVALID: "errors.upload.dimension_invalid",
  AI_PROCESSING_FAILED: "errors.ai.processing_failed",
  NETWORK_ERROR: "errors.network",
  INTERNAL_SERVER_ERROR: "errors.server",
};

const MESSAGE_SUBSTRING_MAP: Array<[RegExp, string]> = [
  [/invalid (email|username) or password/i, "errors.auth.invalid_credentials"],
  [/password reset token is invalid or expired/i, "errors.auth.invalid_reset_token"],
  [/account has been locked/i, "errors.auth.account_locked"],
  [/account is deactivated/i, "errors.auth.account_deactivated"],
  [/old password is incorrect/i, "errors.auth.old_password_incorrect"],
  [/file size exceeds/i, "errors.upload.file_too_large"],
  [/invalid file type|invalid file format/i, "errors.upload.invalid_file"],
  [/image (too small|dimensions)/i, "errors.upload.dimension_invalid"],
  [/image processing failed/i, "errors.ai.processing_failed"],
  [/network error/i, "errors.network"],
];

export const translateBackendError = (
  errorCode: string | undefined,
  rawMessage: string | undefined
): string => {
  if (errorCode && ERROR_CODE_MAP[errorCode]) {
    return i18n.t(ERROR_CODE_MAP[errorCode], { defaultValue: rawMessage || errorCode });
  }
  if (rawMessage) {
    for (const [pattern, key] of MESSAGE_SUBSTRING_MAP) {
      if (pattern.test(rawMessage)) {
        return i18n.t(key, { defaultValue: rawMessage });
      }
    }
  }
  return rawMessage || i18n.t("errors.generic", { defaultValue: "An error occurred" });
};
