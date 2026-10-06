import { useEffect, useState } from 'react'

import { extractErrorDetail } from '../api/client'
import { getMyFavorites } from '../api/posts'
import type { FavoriteItem } from '../api/types'
import { PostCard } from '../components/PostCard'
import { formatDateTime } from '../utils/format'

const SIZE = 10

export function FavoritesPage() {
  const [items, setItems] = useState<FavoriteItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    async function fetchFavorites() {
      try {
        const data = await getMyFavorites({ page, size: SIZE })
        if (!ignore) {
          setItems(data.items)
          setTotal(data.total)
        }
      } catch (err) {
        if (!ignore) setError(extractErrorDetail(err))
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    void fetchFavorites()
    return () => {
      ignore = true
    }
  }, [page])

  const totalPages = Math.max(1, Math.ceil(total / SIZE))

  return (
    <div className="page">
      <h1>我的收藏</h1>
      {error && <p className="error-text">{error}</p>}
      {loading ? (
        <p className="empty-tip">加载中…</p>
      ) : items.length === 0 ? (
        <p className="empty-tip">还没有收藏，去详情页点 ☆ 收藏喜欢的动态吧。</p>
      ) : (
        <>
          <div className="post-list">
            {items.map((item) => (
              <div key={item.id}>
                <PostCard post={item} />
                <p className="favorite-meta">收藏于 {formatDateTime(item.favorited_at)}</p>
              </div>
            ))}
          </div>
          <div className="pager">
            <button
              type="button"
              className="btn btn-ghost"
              disabled={page <= 1}
              onClick={() => {
                setLoading(true)
                setPage((p) => p - 1)
              }}
            >
              上一页
            </button>
            <span>
              {page} / {totalPages}
            </span>
            <button
              type="button"
              className="btn btn-ghost"
              disabled={page >= totalPages}
              onClick={() => {
                setLoading(true)
                setPage((p) => p + 1)
              }}
            >
              下一页
            </button>
          </div>
        </>
      )}
    </div>
  )
}
