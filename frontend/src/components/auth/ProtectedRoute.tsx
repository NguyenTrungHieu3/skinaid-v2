// src/components/auth/ProtectedRoute.tsx
import { type JSX } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

interface ProtectedRouteProps {
  children: JSX.Element;
  requireAdmin?: boolean;
}

const ProtectedRoute = ({ children, requireAdmin = false }: ProtectedRouteProps) => {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    // Nếu chưa đăng nhập , điều hướng về /login
    // "state" giúp chúng ta quay lại trang cũ sau khi login thành công
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check admin role if required
  if (requireAdmin) {
    const userRoles = user?.roles || [];
    const isAdmin = userRoles.some((role: string) => 
      role.toLowerCase() === 'admin'
    );
    
    if (!isAdmin) {
      // If not admin, redirect to home
      return <Navigate to="/" replace />;
    }
  }

  return children; // Nếu đã đăng nhập (và có quyền admin nếu cần), hiển thị trang
};

export default ProtectedRoute;
