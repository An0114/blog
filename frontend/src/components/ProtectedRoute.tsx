/**
 * 页面访问守卫：
 * - <ProtectedRoute>：需登录，未登录跳 /login
 * - <ProtectedRoute adminOnly>：需博主，否则跳首页
 */

import { Navigate, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'

import { useAuth } from '../context/useAuth'

interface ProtectedRouteProps {
  children: ReactNode
  adminOnly?: boolean
}

export function ProtectedRoute({ children, adminOnly = false }: ProtectedRouteProps) {
  const { isLoggedIn, isAdmin } = useAuth()
  const location = useLocation()

  if (!isLoggedIn) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  if (adminOnly && !isAdmin) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}
