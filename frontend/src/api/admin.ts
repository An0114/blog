/**
 * 管理端接口封装（对应 backend routers/admin，仅博主可调用）。
 */

import { api } from './client'
import type { AdminUserListResponse, User, UserStatus } from './types'

export async function listUsers(params: { page?: number; size?: number }): Promise<AdminUserListResponse> {
  const { data } = await api.get<AdminUserListResponse>('/admin/users', { params })
  return data
}

export async function updateUserStatus(userId: number, status: UserStatus): Promise<User> {
  const { data } = await api.patch<User>(`/admin/users/${userId}`, { status })
  return data
}

export async function deleteUser(userId: number): Promise<void> {
  await api.delete(`/admin/users/${userId}`)
}
