import { useEffect, useState } from 'react'

import { listPosts } from '../api/posts'
import type { PostCategory, PostListItem } from '../api/types'
import { extractErrorDetail } from '../api/client'
import { PostCard } from '../components/PostCard'

const SIZE = 10

type CategoryFilter = 'all' | PostCategory

const CATEGORY_OPTIONS: { value: CategoryFilter; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'project', label: '项目' },
  { value: 'daily', label: '日常' },
  { value: 'diary', label: '日记' },
]

export function HomePage() {
  const [posts, setPosts] = useState<PostListItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [category, setCategory] = useState<CategoryFilter>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    async function fetchList() {
      try {
        const data = await listPosts({
          page,
          size: SIZE,
          category: category === 'all' ? undefined : category,
        })
        if (!ignore) {
          setPosts(data.items)
          setTotal(data.total)
        }
      } catch (err) {
        if (!ignore) setError(extractErrorDetail(err))
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    void fetchList()
    return () => {
      ignore = true
    }
  }, [page, category])

  const totalPages = Math.max(1, Math.ceil(total / SIZE))

  return (
    <div>
      <div className="filter-bar">
        {CATEGORY_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            className={`btn ${category === opt.value ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => {
              setLoading(true)
              setCategory(opt.value)
              setPage(1)
            }}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {error && <p className="error-text">{error}</p>}

      {loading ? (
        <p className="empty-tip">加载中…</p>
      ) : posts.length === 0 ? (
        <p className="empty-tip">还没有动态，博主快去发布第一条吧。</p>
      ) : (
        <>
          <div className="post-list">
            {posts.map((post) => (
              <PostCard key={post.id} post={post} />
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
