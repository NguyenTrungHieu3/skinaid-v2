// src/pages/auth/ResetPasswordPage.tsx
import AuthLayout from "./AuthLayout";
import ResetPasswordForm from "../../components/auth/ResetPasswordForm";

const ResetPasswordPage = () => {
  return (
    <AuthLayout align="center">
      <ResetPasswordForm />
    </AuthLayout>
  );
};

export default ResetPasswordPage;
