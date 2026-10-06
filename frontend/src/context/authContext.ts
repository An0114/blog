/**
 * AuthContext 定义（独立文件，满足 react fast-refresh：context 与组件分文件）。
 */

import { createContext } from 'react'

import type { User } from '../api/types'

export interface AuthContextValue {
  user: User | null
  token: string | null
  isLoggedIn: boolean
  isAdmin: boolean
  login: (token: string, user: User) => void
  logout: () => void
  updateUser: (user: User) => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
