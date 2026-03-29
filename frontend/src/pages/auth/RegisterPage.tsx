import AuthLayout from "./AuthLayout";
import AuthTabs from "../../components/auth/AuthTabs";
import RegisterForm from "../../components/auth/RegisterForm"; // <-- Dùng RegisterForm

const RegisterPage = () => {
  return (
    <AuthLayout align="center">
      <AuthTabs active="register" />
      <RegisterForm />
    </AuthLayout>
  );
};

export default RegisterPage;
