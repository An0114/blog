import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { extractErrorDetail } from '../api/client'
import { deleteDraft, listDrafts, publishDraft } from '../api/drafts'
import type { DraftOut } from '../api/types'
import { useAuth } from '../context/useAuth'
import { categoryLabel, formatDateTime } from '../utils/format'

const SIZE = 10

export function DraftsPage() {
  const { isAdmin } = useAuth()
  const navigate = useNavigate()
  const [items, setItems] = useState<DraftOut[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busyId, setBusyId] = useState<number | null>(null)

  useEffect(() => {
    let ignore = false
    async function fetchDrafts() {
      try {
        const data = await listDrafts({ page, size: SIZE })
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
    void fetchDrafts()
    return () => {
      ignore = true
    }
  }, [page])

  if (!isAdmin) {
    return (
      <div className="page">
        <p className="error-text">仅博主可访问草稿箱</p>
      </div>
    )
  }

  const handlePublish = async (draft: DraftOut) => {
    if (busyId !== null) return
    setBusyId(draft.id)
    setError('')
    try {
      const post = await publishDraft(draft.id)
      navigate(`/posts/${post.id}`)
    } catch (err) {
      setError(extractErrorDetail(err))
      setBusyId(null)
    }
  }

  const handleDelete = async (draft: DraftOut) => {
    if (busyId !== null) return
    if (!window.confirm(`删除草稿「${draft.title}」？`)) return
    setBusyId(draft.id)
    setError('')
    try {
      await deleteDraft(draft.id)
      setItems((prev) => prev.filter((d) => d.id !== draft.id))
      setTotal((t) => t - 1)
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setBusyId(null)
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / SIZE))

  return (
    <div className="page">
      <h1>草稿箱</h1>
      {error && <p className="error-text">{error}</p>}
      {loading ? (
        <p className="empty-tip">加载中…</p>
      ) : items.length === 0 ? (
        <p className="empty-tip">还没有草稿，去发布页先写一份吧。</p>
      ) : (
        <>
          <div className="post-list">
            {items.map((draft) => (
              <div key={draft.id} className="post-card">
                <div className="post-card-meta">
                  <span className="badge">{categoryLabel(draft.category)}</span>
                  <span>创建于 {formatDateTime(draft.created_at)}</span>
                  {draft.media_ids.length > 0 && (
                    <span className="form-hint">已选 {draft.media_ids.length} 个媒体</span>
                  )}
                </div>
                <h3>{draft.title}</h3>
                <p className="draft-content">{draft.content}</p>
                <div className="post-card-actions">
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => navigate(`/publish?draft=${draft.id}`)}
                    disabled={busyId !== null}
                  >
                    编辑
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary btn-sm"
                    onClick={() => void handlePublish(draft)}
                    disabled={busyId !== null}
                  >
                    发布
                  </button>
                  <button
                    type="button"
                    className="btn btn-danger btn-sm"
                    onClick={() => void handleDelete(draft)}
                    disabled={busyId !== null}
                  >
                    删除
                  </button>
                </div>
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
