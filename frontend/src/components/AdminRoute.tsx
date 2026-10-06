/**
 * 博主页面访问守卫（PRD A13 / TRD 第 9 节）：
 * - 未登录 → 跳登录页
 * - 普通用户 → 渲染"仅博主可访问"提示（导航不显示，路由层兜底）
 */

import { Navigate } from 'react-router-dom'
import type { ReactNode } from 'react'

import { useAuth } from '../context/useAuth'

interface AdminRouteProps {
  children: ReactNode
}

export function AdminRoute({ children }: AdminRouteProps) {
  const { isLoggedIn, isAdmin } = useAuth()

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />
  }
  if (!isAdmin) {
    return (
      <div className="page">
        <p className="error-text">仅博主可访问该页面</p>
      </div>
    )
  }
  return <>{children}</>
}
