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
