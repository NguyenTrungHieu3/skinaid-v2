export const validateUsername = (username: string) => {
  if (!username) return "Username không được để trống";
  if (username.includes(" ")) return "Username không được chứa khoảng trắng";
  if (username.length < 6) return "Username phải trên 6 ký tự";

  return "";
};

export const validatePassword = (password: string) => {
  if (!password) return "Mật khẩu không được để trống";
  if (password.includes(" ")) return "Mật khẩu không được chứa khoảng trắng";
  if (password.length < 8) return "Mật khẩu phải trên 8 ký tự";

  const regex = /^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])/;
  if (!regex.test(password)) {
    return "Mật khẩu phải có ít nhất 1 chữ hoa, 1 số và 1 ký tự đặc biệt";
  }

  return "";
};

export const validateConfirmPassword = (
  password: string,
  confirmPassword: string
) => {
  if (!confirmPassword) return "Xác nhận mật khẩu không được để trống";
  if (password !== confirmPassword) return "Mật khẩu không khớp";

  return "";
};

export const validateEmail = (email: string) => {
  if (!email) return "Email không được để trống";

  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!regex.test(email)) return "Email không hợp lệ";

  return "";
};

export const validatePhone = (phone: string) => {
  if (!phone) return "Số điện thoại không được để trống";
  const regex = /^(0|\+84)[0-9]{9}$/;
  if (!regex.test(phone.replace(/\s/g, "")))
    return "Số điện thoại không hợp lệ (VD: 0912345678)";
  return "";
};

export const validateBirthDate = (date: string) => {
  if (!date) return "";
  // Chấp nhận dd/mm/yyyy hoặc yyyy-mm-dd
  const ddmmyyyy = /^\d{2}\/\d{2}\/\d{4}$/;
  const yyyymmdd = /^\d{4}-\d{2}-\d{2}$/;
  if (!ddmmyyyy.test(date) && !yyyymmdd.test(date))
    return "Ngày sinh không đúng định dạng (dd/mm/yyyy)";

  let d: Date;
  if (ddmmyyyy.test(date)) {
    const [dd, mm, yyyy] = date.split("/");
    d = new Date(`${yyyy}-${mm}-${dd}`);
  } else {
    d = new Date(date);
  }
  if (isNaN(d.getTime())) return "Ngày sinh không hợp lệ";
  if (d > new Date()) return "Ngày sinh không thể ở tương lai";
  return "";
};

export const validateOldVsNewPassword = (
  oldPassword: string,
  newPassword: string
) => {
  if (oldPassword && newPassword && oldPassword === newPassword)
    return "Mật khẩu mới không được trùng mật khẩu cũ";
  return "";
};
