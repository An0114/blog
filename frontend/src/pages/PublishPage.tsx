import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { extractErrorDetail } from '../api/client'
import { uploadMedia } from '../api/media'
import { createPost } from '../api/posts'
import type { MediaOut, PostCategory } from '../api/types'

interface PendingFile {
  key: number
  file: File
  type: 'image' | 'video'
  previewUrl: string
}

const CATEGORY_OPTIONS: { value: PostCategory; label: string }[] = [
  { value: 'project', label: '项目' },
  { value: 'daily', label: '日常' },
  { value: 'diary', label: '日记' },
]

export function PublishPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [category, setCategory] = useState<PostCategory>('project')
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([])
  const [mediaIds, setMediaIds] = useState<number[]>([])
  const [uploading, setUploading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const nextKey = useRef(1)

  const handleSelectFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files ?? [])
    const next: PendingFile[] = selected.map((file) => ({
      key: nextKey.current++,
      file,
      type: file.type.startsWith('video/') ? 'video' : 'image',
      previewUrl: URL.createObjectURL(file),
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
        uploaded.push(await uploadMedia(p.file, p.type))
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
      navigate(`/posts/${post.id}`)
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setSubmitting(false)
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
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => removePending(p.key)}
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
        <button
          type="submit"
          className="btn btn-primary"
          disabled={submitting || pendingFiles.length > 0}
        >
          {submitting ? '发布中…' : '发布'}
        </button>
        {pendingFiles.length > 0 && (
          <span className="form-hint"> 请先完成媒体上传再发布</span>
        )}
      </form>
    </div>
  )
}
