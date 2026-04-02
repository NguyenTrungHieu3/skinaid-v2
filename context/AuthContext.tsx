import * as SecureStore from "expo-secure-store";
import React, { createContext, useContext, useEffect, useState } from "react";
import { authService } from "../services/authService";

interface AuthContextType {
  user: any;
  token: string | null;
  isLoading: boolean;
  signIn: (data: any) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadStorageData();
  }, []);

  const loadStorageData = async () => {
    try {
      const savedToken = await SecureStore.getItemAsync("userToken");
      if (savedToken) {
        setToken(savedToken);
        // Có thể gọi thêm API /me ở đây để lấy user info mới nhất
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  // Trong file AuthContext.tsx
  const signIn = async (data: any) => {
    const response = await authService.signIn(data);

    // LOG ĐỂ KIỂM TRA (Rất quan trọng)
    console.log("Response Full:", response.data);

    // Theo Swagger Ảnh 4: Dữ liệu nằm trong response.data.data
    const authData = response.data.data;

    if (authData && authData.access_token) {
      const { access_token, user } = authData;

      setToken(access_token);
      setUser(user);

      // Lưu token vào SecureStore
      await SecureStore.setItemAsync("userToken", access_token);

      // Nếu backend có trả về refresh_token, bạn cũng nên lưu lại nếu cần
      if (authData.refresh_token) {
        await SecureStore.setItemAsync("refreshToken", authData.refresh_token);
      }
    } else {
      throw new Error("Không nhận được token từ server");
    }
  };

  const signOut = async () => {
    setToken(null);
    setUser(null);
    await SecureStore.deleteItemAsync("userToken");
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
};
