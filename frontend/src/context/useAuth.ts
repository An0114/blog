/**
 * useAuth hook：读取 AuthContext；独立文件避免与组件混导出。
 */

import { useContext } from 'react'

import { AuthContext, type AuthContextValue } from './authContext'

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (ctx === null) {
    throw new Error('useAuth 必须在 <AuthProvider> 内使用')
  }
  return ctx
}
