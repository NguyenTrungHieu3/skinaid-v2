// src/components/auth/ProtectedRoute.tsx
import { type JSX } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

interface ProtectedRouteProps {
  children: JSX.Element;
  requireAdmin?: boolean;
}

const ProtectedRoute = ({ children, requireAdmin = false }: ProtectedRouteProps) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  console.log("🔍 [ProtectedRoute]", {
    isLoading,
    isAuthenticated,
    hasUser: !!user,
    requireAdmin,
    pathname: location.pathname
  });

  // Show loading screen while checking authentication
  if (isLoading) {
    console.log("⏳ [ProtectedRoute] Still loading, showing loading screen");
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    console.log("❌ [ProtectedRoute] Not authenticated, redirecting to login");
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

    console.log("🔍 [ProtectedRoute] Admin check", { userRoles, isAdmin });

    if (!isAdmin) {
      console.log("❌ [ProtectedRoute] Not admin, redirecting to home");
      // If not admin, redirect to home
      return <Navigate to="/" replace />;
    }
  }

  console.log("✅ [ProtectedRoute] Access granted");
  return children; // Nếu đã đăng nhập (và có quyền admin nếu cần), hiển thị trang
};

export default ProtectedRoute;
