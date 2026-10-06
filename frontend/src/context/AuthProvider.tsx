/**
 * 登录态 Provider：从 localStorage 恢复会话，提供 login/logout。
 * 使用方式：<AuthProvider> 包裹应用，页面内 useAuth()（见 useAuth.ts）。
 */

import { useCallback, useMemo, useState, type ReactNode } from 'react'

import {
  clearSession,
  getStoredToken,
  getStoredUser,
  storeSession,
} from '../api/client'
import type { User } from '../api/types'
import { AuthContext } from './authContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => getStoredUser())
  const [token, setToken] = useState<string | null>(() => getStoredToken())

  const login = useCallback((nextToken: string, nextUser: User) => {
    storeSession(nextToken, nextUser)
    setToken(nextToken)
    setUser(nextUser)
  }, [])

  const logout = useCallback(() => {
    clearSession()
    setToken(null)
    setUser(null)
  }, [])

  // 更新当前用户信息（如邮箱验证后刷新 email_verified）
  const updateUser = useCallback((nextUser: User) => {
    storeSession(getStoredToken() ?? '', nextUser)
    setUser(nextUser)
  }, [])

  const value = useMemo(
    () => ({
      user,
      token,
      isLoggedIn: token !== null && user !== null,
      isAdmin: user?.role === 'admin',
      login,
      logout,
      updateUser,
    }),
    [user, token, login, logout, updateUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
