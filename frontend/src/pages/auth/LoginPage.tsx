import { useEffect } from "react";
import AuthLayout from "./AuthLayout";
import AuthTabs from "../../components/auth/AuthTabs";
import LoginForm from "../../components/auth/LoginForm";

const LoginPage = () => {
  // Check for logout reason (debug purpose)
  useEffect(() => {
    const logoutReason = sessionStorage.getItem('logout_reason');
    if (logoutReason) {
      try {
        const { error, details, timestamp } = JSON.parse(logoutReason);
        console.error('=== LOGOUT REASON ===');
        console.error('Error:', error);
        console.error('Details:', details);
        console.error('Timestamp:', timestamp);
        console.error('====================');
        // Clear after showing
        sessionStorage.removeItem('logout_reason');
      } catch (e) {
        console.error('Failed to parse logout reason:', e);
      }
    }
  }, []);

  return (
    <AuthLayout align="center">
      <AuthTabs active="login" />
      <LoginForm />
    </AuthLayout>
  );
};

export default LoginPage;
