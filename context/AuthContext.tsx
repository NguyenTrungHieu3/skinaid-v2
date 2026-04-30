import * as SecureStore from "expo-secure-store";
import React, { createContext, useContext, useEffect, useState } from "react";
import { authService } from "../services/authService";
import type { SignInPayload, User } from "../constants/types";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  signIn: (data: SignInPayload, rememberMe: boolean) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadStorageData();
  }, []);

  const loadStorageData = async () => {
    try {
      const savedToken = await SecureStore.getItemAsync("userToken");
      const savedRemember = await SecureStore.getItemAsync("rememberMe");
      const isRemember = savedRemember ? JSON.parse(savedRemember) : true;

      if (savedToken && isRemember) {
        setToken(savedToken);
        const res = await authService.getMe(savedToken);
        setUser(res.data?.data || res.data);
      }
    } catch {
      await SecureStore.deleteItemAsync("userToken");
      await SecureStore.deleteItemAsync("refreshToken");
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const signIn = async (data: SignInPayload, rememberMe: boolean) => {
    const response = await authService.signIn(data);
    const authData = response.data?.data || response.data;

    if (authData && authData.access_token) {
      const { access_token, refresh_token, user: userData } = authData;

      setToken(access_token);
      setUser(userData);

      await SecureStore.setItemAsync("rememberMe", JSON.stringify(rememberMe));

      if (rememberMe) {
        await SecureStore.setItemAsync("userToken", access_token);
        if (refresh_token) {
          await SecureStore.setItemAsync("refreshToken", refresh_token);
        }
      }
    } else {
      throw new Error("Không nhận được token từ server");
    }
  };

  const signOut = async () => {
    try {
      await authService.logout();
    } catch {
      // Ignore logout API errors — still clear local state
    }
    setToken(null);
    setUser(null);
    await SecureStore.deleteItemAsync("userToken");
    await SecureStore.deleteItemAsync("refreshToken");
    await SecureStore.deleteItemAsync("rememberMe");
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
