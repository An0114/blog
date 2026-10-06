/**
 * 动态与评论接口封装（对应 backend routers/posts、comments）。
 */

import { api } from './client'
import type {
  CommentOut,
  FavoriteListResponse,
  FavoriteResponse,
  LikeResponse,
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

/** 点赞 / 取消点赞（toggle，需登录；二期功能）。 */
export async function toggleLike(postId: number): Promise<LikeResponse> {
  const { data } = await api.post<LikeResponse>(`/posts/${postId}/like`)
  return data
}

/** 收藏 / 取消收藏（toggle，需登录；三期功能）。 */
export async function toggleFavorite(postId: number): Promise<FavoriteResponse> {
  const { data } = await api.post<FavoriteResponse>(`/posts/${postId}/favorite`)
  return data
}

/** 我的收藏列表（需登录，分页）。 */
export async function getMyFavorites(params: {
  page?: number
  size?: number
}): Promise<FavoriteListResponse> {
  const { data } = await api.get<FavoriteListResponse>('/me/favorites', { params })
  return data
}
