// src/components/auth/PublicRoute.tsx
import { type JSX } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

const PublicRoute = ({ children }: { children: JSX.Element }) => {
  const { isAuthenticated, user } = useAuth();

  // 3. Sửa điều kiện: "if (isAuthenticated)"
  if (isAuthenticated) {
    // Check if user is admin
    const userRoles = user?.roles || [];
    const isAdmin = userRoles.some((role: string) => 
      role.toLowerCase() === 'admin'
    );
    
    // Nếu ĐÃ đăng nhập, điều hướng dựa trên role
    if (isAdmin) {
      return <Navigate to="/admin" replace />;
    }
    return <Navigate to="/" replace />;
  }

  // Nếu CHƯA đăng nhập, hiển thị trang (login/register)
  return children;
};

export default PublicRoute;
