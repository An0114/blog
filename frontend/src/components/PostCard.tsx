import { Link } from 'react-router-dom'

import type { PostListItem } from '../api/types'
import { categoryLabel, formatDateTime } from '../utils/format'

interface PostCardProps {
  post: PostListItem
}

/** 动态摘要：截断到 80 字（纯文本）。 */
function excerpt(content: string, max = 80): string {
  const text = content.replace(/\s+/g, ' ').trim()
  return text.length > max ? `${text.slice(0, max)}…` : text
}

export function PostCard({ post }: PostCardProps) {
  return (
    <article className="post-card">
      <h2 className="post-card-title">
        <Link to={`/posts/${post.id}`}>{post.title}</Link>
      </h2>
      <div className="post-card-meta">
        <span className="badge">{categoryLabel(post.category)}</span>
        <span>{formatDateTime(post.created_at)}</span>
        <span>♥ {post.like_count}</span>
        <span>☆ {post.favorite_count}</span>
      </div>
      <p className="post-card-excerpt">{excerpt(post.content)}</p>
      {post.cover_url && (
        <Link to={`/posts/${post.id}`}>
          <img
            src={post.cover_url}
            alt="封面"
            className="post-card-cover"
            loading="lazy"
          />
        </Link>
      )}
    </article>
  )
}
