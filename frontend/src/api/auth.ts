/**
 * 认证接口封装（对应 backend routers/auth）。
 */

import { api } from './client'
import type { AuthResponse, LoginRequest, RegisterRequest, User } from './types'

export async function register(payload: RegisterRequest): Promise<User> {
  const { data } = await api.post<User>('/auth/register', payload)
  return data
}

export async function login(payload: LoginRequest): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/login', payload)
  return data
}

/** 发送邮箱验证链接（需登录；未配置 SMTP 时链接出现在后端日志）。 */
export async function requestVerifyEmail(): Promise<{ message: string; expires_minutes: number }> {
  const { data } = await api.post<{ message: string; expires_minutes: number }>(
    '/auth/verify-email/request',
  )
  return data
}

/** 凭 token 完成邮箱验证，返回更新后的用户信息。 */
export async function confirmVerifyEmail(token: string): Promise<User> {
  const { data } = await api.post<User>('/auth/verify-email/confirm', { token })
  return data
}

/** 找回密码：向邮箱发送重置链接（邮箱不存在也返回成功，防枚举）。 */
export async function forgotPassword(email: string): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/auth/forgot-password', { email })
  return data
}

/** 凭 token 重置密码。 */
export async function resetPassword(token: string, newPassword: string): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/auth/reset-password', {
    token,
    new_password: newPassword,
  })
  return data
}
