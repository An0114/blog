/**
 * 草稿箱接口封装（对应 backend routers/drafts，三期功能，仅博主）。
 */

import { api } from './client'
import type { DraftCreate, DraftListResponse, DraftOut, PostOut } from './types'

export async function createDraft(payload: DraftCreate): Promise<DraftOut> {
  const { data } = await api.post<DraftOut>('/drafts', payload)
  return data
}

export async function listDrafts(params: { page?: number; size?: number }): Promise<DraftListResponse> {
  const { data } = await api.get<DraftListResponse>('/drafts', { params })
  return data
}

export async function getDraft(id: number): Promise<DraftOut> {
  const { data } = await api.get<DraftOut>(`/drafts/${id}`)
  return data
}

export async function updateDraft(id: number, payload: DraftCreate): Promise<DraftOut> {
  const { data } = await api.put<DraftOut>(`/drafts/${id}`, payload)
  return data
}

export async function deleteDraft(id: number): Promise<void> {
  await api.delete(`/drafts/${id}`)
}

/** 发布草稿：生成动态并绑定媒体，成功后草稿删除。 */
export async function publishDraft(id: number): Promise<PostOut> {
  const { data } = await api.post<PostOut>(`/drafts/${id}/publish`)
  return data
}
