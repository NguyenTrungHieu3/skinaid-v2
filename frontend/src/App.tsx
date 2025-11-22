import { Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import RegisterPage from "./pages/auth/RegisterPage";
import LoginPage from "./pages/auth/LoginPage";
import ForgotPasswordPage from "./pages/auth/ForgotPasswordPage";
import ResetPasswordPage from "./pages/auth/ResetPasswordPage";
import PublicRoute from "./components/auth/PublicRoute";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import MainLayout from "./components/layout/MainLayout"; // Component layout chính
import UploadPage from "./pages/UploadPage";
import ProfilePage from "./pages/ProfilePage";
import AnalysisResultPage from "./pages/AnalysisResultPage";
import HistoryPage from "./pages/HistoryPage";
import AdminPage from "./pages/AdminPage";

function App() {
  return (
    // Xóa <div> và <main> không cần thiết
    <Routes>
      {/* === CÁC TRANG CÓ HEADER VÀ FOOTER (Dùng MainLayout) === */}
      <Route element={<MainLayout />}>
        <Route
          path="/"
          element={
            <>
              <HomePage />
              {/* <Footer /> Footer CHỈ hiển thị cùng HomePage */}
            </>
          }
        />
        <Route path="/upload" element={<UploadPage />} />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <HistoryPage />
            </ProtectedRoute>
          }
        />
        {/* Thêm các trang khác cần Header vào đây (ví dụ: /about) */}
      </Route>

      {/* === CÁC TRANG KHÔNG CÓ HEADER (Layout riêng) === */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        }
      />
      <Route
        path="/forgot-password"
        element={
          <PublicRoute>
            <ForgotPasswordPage />
          </PublicRoute>
        }
      />
      <Route
        path="/reset-password"
        element={
          <PublicRoute>
            {/* Bạn đã quên bọc PublicRoute ở đây */}
            <ResetPasswordPage />
          </PublicRoute>
        }
      />

      {/* Trang Analysis Result có layout sidebar riêng */}
      <Route
        path="/analysis-result/:analysis_id"
        element={<AnalysisResultPage />}
      />

      {/* Trang Admin - Protected route chỉ cho admin */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute requireAdmin={true}>
            <AdminPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;
