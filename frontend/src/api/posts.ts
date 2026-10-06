/**
 * 动态与评论接口封装（对应 backend routers/posts、comments）。
 */

import { api } from './client'
import type {
  CommentOut,
  PostCategory,
  PostCreate,
  PostListResponse,
  PostOut,
} from './types'

export async function listPosts(params: {
  page?: number
  size?: number
  category?: PostCategory
}): Promise<PostListResponse> {
  const { data } = await api.get<PostListResponse>('/posts', { params })
  return data
}

export async function getPost(id: number): Promise<PostOut> {
  const { data } = await api.get<PostOut>(`/posts/${id}`)
  return data
}

export async function createPost(payload: PostCreate): Promise<PostOut> {
  const { data } = await api.post<PostOut>('/posts', payload)
  return data
}

export async function deletePost(id: number): Promise<void> {
  await api.delete(`/posts/${id}`)
}

export async function createComment(postId: number, content: string): Promise<CommentOut> {
  const { data } = await api.post<CommentOut>(`/posts/${postId}/comments`, { content })
  return data
}

export async function deleteComment(commentId: number): Promise<void> {
  await api.delete(`/comments/${commentId}`)
}
