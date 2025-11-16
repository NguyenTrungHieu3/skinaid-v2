// src/components/auth/PublicRoute.tsx
import { type JSX } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

const PublicRoute = ({ children }: { children: JSX.Element }) => {
  const { isAuthenticated } = useAuth();

  // 3. Sửa điều kiện: "if (isAuthenticated)"
  if (isAuthenticated) {
    // Nếu ĐÃ đăng nhập, điều hướng về homepage
    return <Navigate to="/" replace />;
  }

  // Nếu CHƯA đăng nhập, hiển thị trang (login/register)
  return children;
};

export default PublicRoute;
