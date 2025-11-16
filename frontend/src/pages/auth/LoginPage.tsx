import AuthLayout from "./AuthLayout";
import AuthTabs from "../../components/auth/AuthTabs";
import LoginForm from "../../components/auth/LoginForm";

const LoginPage = () => {
  return (
    <AuthLayout align="center">
      <AuthTabs active="login" />
      <LoginForm />
    </AuthLayout>
  );
};

export default LoginPage;
