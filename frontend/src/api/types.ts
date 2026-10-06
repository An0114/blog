/**
 * 与后端 API 对齐的前端类型（对应 backend/app/schemas/*，见 TRD 第 4 节）。
 * 字段命名与后端响应 JSON 保持一致（snake_case）。
 */

export type UserRole = 'admin' | 'user'
export type UserStatus = 'active' | 'disabled' | 'deleted'
export type PostCategory = 'project' | 'daily' | 'diary'
export type MediaType = 'image' | 'video'

export interface User {
  id: number
  username: string
  email: string
  role: UserRole
  status: UserStatus
  email_verified: boolean
  created_at: string
}

export interface MediaOut {
  id: number
  post_id: number | null
  media_type: MediaType
  url: string
  created_at: string
}

export interface CommentOut {
  id: number
  post_id: number
  user_id: number
  username: string
  content: string
  created_at: string
}

export interface PostListItem {
  id: number
  title: string
  content: string
  category: PostCategory
  cover_url: string | null
  like_count: number
  favorite_count: number
  created_at: string
  updated_at: string
}

export interface PostListResponse {
  items: PostListItem[]
  total: number
  page: number
  size: number
}

export interface PostOut {
  id: number
  author_id: number
  title: string
  content: string
  category: PostCategory
  created_at: string
  updated_at: string
  media: MediaOut[]
  comments: CommentOut[]
  like_count: number
  liked: boolean
  favorite_count: number
  favorited: boolean
}

export interface LikeResponse {
  liked: boolean
  like_count: number
}

export interface FavoriteResponse {
  favorited: boolean
  favorite_count: number
}

export interface FavoriteItem extends PostListItem {
  favorited_at: string
}

export interface FavoriteListResponse {
  items: FavoriteItem[]
  total: number
  page: number
  size: number
}

export interface PostCreate {
  title: string
  content: string
  category: PostCategory
  media_ids?: number[]
}

export interface CommentCreate {
  content: string
}

export interface AuthResponse {
  token: string
  user: User
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface AdminUserListResponse {
  items: User[]
  total: number
  page: number
  size: number
}

export interface AdminCommentOut {
  id: number
  post_id: number
  post_title: string
  user_id: number
  username: string
  content: string
  created_at: string
}

export interface AdminCommentListResponse {
  items: AdminCommentOut[]
  total: number
  page: number
  size: number
}
