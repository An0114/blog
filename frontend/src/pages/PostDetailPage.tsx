import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { extractErrorDetail } from '../api/client'
import { createComment, deleteComment, deletePost, getPost, toggleLike } from '../api/posts'
import type { PostOut } from '../api/types'
import { useAuth } from '../context/useAuth'
import { categoryLabel, formatDateTime } from '../utils/format'

export function PostDetailPage() {
  const { id } = useParams<{ id: string }>()
  const postId = Number(id)
  const { user, isAdmin, isLoggedIn } = useAuth()
  const navigate = useNavigate()

  const [post, setPost] = useState<PostOut | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [commentText, setCommentText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [liking, setLiking] = useState(false)

  useEffect(() => {
    let ignore = false
    async function fetchDetail() {
      try {
        const detail = await getPost(postId)
        if (!ignore) setPost(detail)
      } catch (err) {
        if (!ignore) setError(extractErrorDetail(err))
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    void fetchDetail()
    return () => {
      ignore = true
    }
  }, [postId])

  const handleCommentSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const content = commentText.trim()
    if (!content || !post || submitting) return
    setSubmitting(true)
    try {
      const comment = await createComment(post.id, content)
      setPost((prev) => (prev ? { ...prev, comments: [...prev.comments, comment] } : prev))
      setCommentText('')
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setSubmitting(false)
    }
  }

  const handleCommentDelete = async (commentId: number) => {
    if (!post) return
    try {
      await deleteComment(commentId)
      setPost((prev) =>
        prev ? { ...prev, comments: prev.comments.filter((c) => c.id !== commentId) } : prev,
      )
    } catch (err) {
      setError(extractErrorDetail(err))
    }
  }

  const handlePostDelete = async () => {
    if (!post) return
    try {
      await deletePost(post.id)
      navigate('/')
    } catch (err) {
      setError(extractErrorDetail(err))
    }
  }

  const handleToggleLike = async () => {
    if (!isLoggedIn) {
      navigate('/login')
      return
    }
    if (!post || liking) return
    setLiking(true)
    try {
      const result = await toggleLike(post.id)
      setPost((prev) =>
        prev ? { ...prev, liked: result.liked, like_count: result.like_count } : prev,
      )
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setLiking(false)
    }
  }

  if (loading) return <p className="empty-tip">加载中…</p>
  if (error || !post) {
    return (
      <div className="page">
        <p className="error-text">{error || '动态不存在'}</p>
        <Link to="/">返回首页</Link>
      </div>
    )
  }

  return (
    <article className="page">
      <h1>{post.title}</h1>
      <div className="post-card-meta">
        <span className="badge">{categoryLabel(post.category)}</span>
        <span>{formatDateTime(post.created_at)}</span>
        <button
          type="button"
          className={`btn btn-sm ${post.liked ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => void handleToggleLike()}
          disabled={liking}
        >
          {post.liked ? '♥ 已赞' : '♡ 点赞'} · {post.like_count}
        </button>
        {isAdmin && post.author_id === user?.id && (
          <button type="button" className="btn btn-danger btn-sm" onClick={() => void handlePostDelete()}>
            删除动态
          </button>
        )}
      </div>
      <div className="detail-content">{post.content}</div>

      {post.media.length > 0 && (
        <div className="detail-media">
          {post.media.map((m) =>
            m.media_type === 'video' ? (
              <video key={m.id} src={m.url} controls preload="metadata" />
            ) : (
              <img key={m.id} src={m.url} alt="动态图片" />
            ),
          )}
        </div>
      )}

      <h2>评论（{post.comments.length}）</h2>
      {isLoggedIn ? (
        <form className="comment-form" onSubmit={handleCommentSubmit}>
          <input
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            placeholder="写下你的评论…"
            maxLength={500}
          />
          <button type="submit" className="btn btn-primary" disabled={submitting || !commentText.trim()}>
            发表
          </button>
        </form>
      ) : (
        <p className="empty-tip">
          <Link to="/login">登录</Link> 后参与评论
        </p>
      )}

      {post.comments.length === 0 ? (
        <p className="empty-tip">暂无评论</p>
      ) : (
        <div className="comment-list">
          {post.comments.map((comment) => (
            <div key={comment.id} className="comment-item">
              <div className="comment-meta">
                <strong>{comment.username}</strong> · {formatDateTime(comment.created_at)}
                {(user?.id === comment.user_id || isAdmin) && (
                  <button
                    type="button"
                    className="btn btn-ghost comment-delete"
                    onClick={() => void handleCommentDelete(comment.id)}
                  >
                    删除
                  </button>
                )}
              </div>
              <div>{comment.content}</div>
            </div>
          ))}
        </div>
      )}
    </article>
  )
}
