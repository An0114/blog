/**
 * 站点初始化页 /admin/init（PRD A16 / TRD Task 16）：
 * - 无管理员账户时开放：创建博主账户 + 网站图标 + 邮箱验证开关（含 SMTP 配置）；
 * - 已初始化时仅显示提示并引导登录；
 * - 主题与全站一致（深色文艺纸卡），路由独立于 Layout（无侧栏）。
 */

import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { extractErrorDetail } from '../api/client'
import { getInitStatus, initialize } from '../api/init'
import { SiteLogo } from '../components/SiteLogo'

// 图标白名单与大小限制（与后端一致）
const ICON_ACCEPT = ['image/png', 'image/jpeg', 'image/webp', 'image/x-icon']
const ICON_MAX_BYTES = 1024 * 1024

export function InitPage() {
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [initialized, setInitialized] = useState(false)
  const [statusError, setStatusError] = useState('')

  // 博主账户
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')

  // 站点配置
  const [iconDataUrl, setIconDataUrl] = useState('')
  const [emailVerify, setEmailVerify] = useState(false)
  const [smtpHost, setSmtpHost] = useState('')
  const [smtpPort, setSmtpPort] = useState('465')
  const [smtpUser, setSmtpUser] = useState('')
  const [smtpPassword, setSmtpPassword] = useState('')

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    getInitStatus()
      .then((status) => {
        if (!cancelled) {
          setInitialized(status.initialized)
          setLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setStatusError(extractErrorDetail(err))
          setLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  const handleIcon = (file: File | undefined) => {
    if (!file) return
    if (!ICON_ACCEPT.includes(file.type)) {
      setError('网站图标仅支持 png / jpg / webp / ico 格式')
      return
    }
    if (file.size > ICON_MAX_BYTES) {
      setError('网站图标不超过 1MB')
      return
    }
    setError('')
    const reader = new FileReader()
    reader.onload = () => {
      setIconDataUrl(typeof reader.result === 'string' ? reader.result : '')
    }
    reader.readAsDataURL(file)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (submitting) return
    if (password !== confirm) {
      setError('两次输入的密码不一致')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      await initialize({
        username: username.trim(),
        email: email.trim(),
        password,
        ...(iconDataUrl ? { site_icon_base64: iconDataUrl } : {}),
        email_verify_enabled: emailVerify,
        ...(emailVerify
          ? {
              smtp_host: smtpHost.trim(),
              smtp_port: Number(smtpPort) || undefined,
              smtp_user: smtpUser.trim(),
              smtp_password: smtpPassword,
            }
          : {}),
      })
      navigate('/login', { state: { initialized: true } })
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <p className="empty-tip">检查站点状态…</p>
  }
  if (statusError) {
    return (
      <div className="init-wrap">
        <div className="page init-card">
          <p className="error-text">{statusError}</p>
        </div>
      </div>
    )
  }

  if (initialized) {
    return (
      <div className="init-wrap">
        <div className="page init-card">
          <p className="success-text">站点已初始化</p>
          <p className="form-hint">博主账户已存在，请直接登录。</p>
          <Link to="/login" className="btn btn-primary">
            去登录
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="init-wrap">
      <div className="page init-card">
        <div className="init-head">
          <SiteLogo size={72} />
          <h1>初始化博客</h1>
          <p className="form-hint">创建你的博主账户，开启「未完成的页」</p>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="init-username">用户名</label>
            <input
              id="init-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              minLength={3}
              maxLength={30}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="init-email">邮箱</label>
            <input
              id="init-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="init-password">密码（至少 6 位）</label>
            <input
              id="init-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={6}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="init-confirm">确认密码</label>
            <input
              id="init-confirm"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              minLength={6}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="init-icon">网站图标（可选，png / jpg / webp / ico ≤1MB）</label>
            <input
              id="init-icon"
              type="file"
              accept="image/png,image/jpeg,image/webp,image/x-icon"
              onChange={(e) => handleIcon(e.target.files?.[0])}
            />
            {iconDataUrl && (
              <img src={iconDataUrl} alt="网站图标预览" className="init-icon-preview" />
            )}
          </div>

          <div className="field">
            <label className="switch">
              <input
                type="checkbox"
                checked={emailVerify}
                onChange={(e) => setEmailVerify(e.target.checked)}
              />
              <span className="switch-slider" />
              <span className="switch-label">用户注册需要邮箱验证</span>
            </label>
            <p className="form-hint">开启后，新用户注册需验证邮箱才能登录（默认关闭）。</p>
          </div>

          {emailVerify && (
            <div className="smtp-box">
              <p className="smtp-title">SMTP 邮件配置</p>
              <div className="smtp-grid">
                <div className="field">
                  <label htmlFor="smtp-host">SMTP 主机</label>
                  <input
                    id="smtp-host"
                    type="text"
                    value={smtpHost}
                    onChange={(e) => setSmtpHost(e.target.value)}
                    placeholder="smtp.example.com"
                    required={emailVerify}
                  />
                </div>
                <div className="field">
                  <label htmlFor="smtp-port">端口</label>
                  <input
                    id="smtp-port"
                    type="number"
                    value={smtpPort}
                    onChange={(e) => setSmtpPort(e.target.value)}
                    min={1}
                    max={65535}
                    required={emailVerify}
                  />
                </div>
                <div className="field">
                  <label htmlFor="smtp-user">邮箱账号</label>
                  <input
                    id="smtp-user"
                    type="text"
                    value={smtpUser}
                    onChange={(e) => setSmtpUser(e.target.value)}
                    required={emailVerify}
                  />
                </div>
                <div className="field">
                  <label htmlFor="smtp-password">邮箱密码 / 授权码</label>
                  <input
                    id="smtp-password"
                    type="password"
                    value={smtpPassword}
                    onChange={(e) => setSmtpPassword(e.target.value)}
                    required={emailVerify}
                  />
                </div>
              </div>
            </div>
          )}

          {error && <p className="error-text">{error}</p>}
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? '初始化中…' : '完成初始化'}
          </button>
        </form>
      </div>
    </div>
  )
}
