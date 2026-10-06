import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { extractErrorDetail } from '../api/client'
import { createDraft, deleteDraft, getDraft, updateDraft } from '../api/drafts'
import { uploadMedia } from '../api/media'
import { createPost } from '../api/posts'
import type { MediaOut, PostCategory } from '../api/types'
import { readingMinutes } from '../utils/format'

interface PendingFile {
  key: number
  file: File
  type: 'image' | 'video'
  previewUrl: string
  progress: number | null // 上传进度 0-100；null 表示尚未上传
}

const CATEGORY_OPTIONS: { value: PostCategory; label: string }[] = [
  { value: 'project', label: '项目' },
  { value: 'daily', label: '日常' },
  { value: 'diary', label: '日记' },
]

export function PublishPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const draftId = searchParams.get('draft') ? Number(searchParams.get('draft')) : null
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [category, setCategory] = useState<PostCategory>('project')
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([])
  const [mediaIds, setMediaIds] = useState<number[]>([])
  const [uploading, setUploading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [savingDraft, setSavingDraft] = useState(false)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const nextKey = useRef(1)

  // 草稿编辑模式：加载草稿内容回填表单（媒体 id 已上传待绑定，直接沿用）
  useEffect(() => {
    if (draftId === null) return
    const id = draftId // 显式收窄：TS 不把 const 联合类型的收窄传播进异步闭包
    let ignore = false
    async function loadDraft() {
      try {
        const draft = await getDraft(id)
        if (ignore) return
        setTitle(draft.title)
        setContent(draft.content)
        setCategory(draft.category)
        setMediaIds(draft.media_ids)
      } catch (err) {
        if (!ignore) setError(extractErrorDetail(err))
      }
    }
    void loadDraft()
    return () => {
      ignore = true
    }
  }, [draftId])

  const handleSelectFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files ?? [])
    const next: PendingFile[] = selected.map((file) => ({
      key: nextKey.current++,
      file,
      type: file.type.startsWith('video/') ? 'video' : 'image',
      previewUrl: URL.createObjectURL(file),
      progress: null,
    }))
    setPendingFiles((prev) => [...prev, ...next])
    e.target.value = '' // 允许重复选择同一文件
  }

  const removePending = (key: number) => {
    setPendingFiles((prev) => {
      const target = prev.find((p) => p.key === key)
      if (target) URL.revokeObjectURL(target.previewUrl)
      return prev.filter((p) => p.key !== key)
    })
  }

  const handleUpload = async () => {
    if (pendingFiles.length === 0 || uploading) return
    setUploading(true)
    setError('')
    setInfo('')
    try {
      const uploaded: MediaOut[] = []
      for (const p of pendingFiles) {
        // 逐文件上传并实时回写进度（PRD A12：附件上传进度）
        const media = await uploadMedia(p.file, p.type, (percent) => {
          setPendingFiles((prev) =>
            prev.map((item) => (item.key === p.key ? { ...item, progress: percent } : item)),
          )
        })
        uploaded.push(media)
      }
      setMediaIds((prev) => [...prev, ...uploaded.map((m) => m.id)])
      pendingFiles.forEach((p) => URL.revokeObjectURL(p.previewUrl))
      setPendingFiles([])
      setInfo(`已上传 ${uploaded.length} 个媒体文件`)
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setUploading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (submitting) return
    setSubmitting(true)
    setError('')
    setInfo('')
    try {
      const post = await createPost({
        title: title.trim(),
        content: content.trim(),
        category,
        media_ids: mediaIds.length > 0 ? mediaIds : undefined,
      })
      // 草稿编辑模式下发布：清理已发布的草稿，避免残留
      if (draftId) {
        await deleteDraft(draftId).catch(() => undefined)
      }
      navigate(`/posts/${post.id}`)
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setSubmitting(false)
    }
  }

  const handleSaveDraft = async () => {
    if (savingDraft || !title.trim() || !content.trim()) return
    setSavingDraft(true)
    setError('')
    setInfo('')
    try {
      const payload = {
        title: title.trim(),
        content: content.trim(),
        category,
        media_ids: mediaIds,
      }
      if (draftId) {
        await updateDraft(draftId, payload)
        setInfo('草稿已更新')
      } else {
        await createDraft(payload)
        setInfo('草稿已保存')
      }
      navigate('/drafts')
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setSavingDraft(false)
    }
  }

  return (
    <div className="page">
      <h1>发布动态</h1>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="title">标题</label>
          <input
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={120}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="category">分类</label>
          <select
            id="category"
            value={category}
            onChange={(e) => setCategory(e.target.value as PostCategory)}
          >
            {CATEGORY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="content">正文</label>
          <textarea
            id="content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            required
          />
        </div>

        <div className="field">
          <label>媒体（可选，图片 ≤10MB / 视频 ≤100MB）</label>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,video/mp4,video/webm"
            multiple
            onChange={handleSelectFiles}
          />
          {pendingFiles.length > 0 && (
            <div className="media-pending">
              {pendingFiles.map((p) => (
                <div key={p.key} className="media-pending-item">
                  {p.type === 'video' ? (
                    <video src={p.previewUrl} muted />
                  ) : (
                    <img src={p.previewUrl} alt="待上传" />
                  )}
                  {p.progress !== null && p.progress < 100 && (
                    <div className="upload-progress">
                      <div
                        className="upload-progress-bar"
                        style={{ width: `${p.progress}%` }}
                      />
                      <span>{p.progress}%</span>
                    </div>
                  )}
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => removePending(p.key)}
                    disabled={uploading}
                  >
                    移除
                  </button>
                </div>
              ))}
              <button type="button" className="btn btn-ghost" onClick={() => void handleUpload()} disabled={uploading}>
                {uploading ? '上传中…' : '上传到服务器'}
              </button>
            </div>
          )}
          {info && <p className="success-text">{info}</p>}
        </div>

        {error && <p className="error-text">{error}</p>}
        <div className="publish-actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting || pendingFiles.length > 0}
          >
            {submitting ? '发布中…' : '发布'}
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => void handleSaveDraft()}
            disabled={savingDraft || !title.trim() || !content.trim()}
          >
            {savingDraft ? '保存中…' : draftId ? '更新草稿' : '存为草稿'}
          </button>
          {draftId && (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => navigate('/drafts')}
            >
              返回草稿箱
            </button>
          )}
        </div>
        {pendingFiles.length > 0 && (
          <span className="form-hint"> 请先完成媒体上传再发布</span>
        )}
        <div className="publish-stats">
          <span>已写 {content.replace(/\s+/g, '').length} 字</span>
          <span>预估阅读 {readingMinutes(content)} 分钟</span>
        </div>
      </form>
    </div>
  )
}
