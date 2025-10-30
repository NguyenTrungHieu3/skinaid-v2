import React, { useEffect } from "react";
import "../../assets/styles/components/errorbanner.scss";

function ErrorBanner({ message, onClose }) {
  useEffect(() => {
    if (!message) return;

    const timer = setTimeout(() => {
      onClose(); // ẩn sau 3 giây
    }, 3000);

    return () => clearTimeout(timer);
  }, [message, onClose]);

  if (!message) return null;

  return (
    <div className="error-banner">
      <span>{message}</span>
      <button className="close-btn" onClick={onClose}>
        ✕
      </button>
    </div>
  );
}

export default ErrorBanner;

