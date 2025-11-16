// src/components/auth/ProtectedRoute.tsx
import { type JSX } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    // Nếu chưa đăng nhập , điều hướng về /login
    // "state" giúp chúng ta quay lại trang cũ sau khi login thành công
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children; // Nếu đã đăng nhập, hiển thị trang
};

export default ProtectedRoute;
