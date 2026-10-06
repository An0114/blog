/**
 * 管理端接口封装（对应 backend routers/admin，仅博主可调用）。
 */

import { api } from './client'
import type {
  AdminCommentListResponse,
  AdminUserListResponse,
  User,
  UserStatus,
} from './types'

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

/** 评论管理：全站评论列表（仅博主；二期功能）。 */
export async function listAdminComments(params: {
  page?: number
  size?: number
}): Promise<AdminCommentListResponse> {
  const { data } = await api.get<AdminCommentListResponse>('/admin/comments', { params })
  return data
}

export async function deleteAdminComment(commentId: number): Promise<void> {
  await api.delete(`/admin/comments/${commentId}`)
}
