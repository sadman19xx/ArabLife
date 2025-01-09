import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  user: any | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, user: any) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
}

const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: (token, user) =>
        set({
          token,
          user,
          isAuthenticated: true,
          isLoading: false,
        }),
      logout: () =>
        set({
          token: null,
          user: null,
          isAuthenticated: false,
          isLoading: false,
        }),
      setLoading: (loading) =>
        set({
          isLoading: loading,
        }),
    }),
    {
      name: 'auth-storage',
    }
  )
);

export default useAuth;
