import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { resetPassword } from '../api/auth'
import { extractErrorDetail } from '../api/client'

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (busy) return
    if (password !== confirm) {
      setError('两次输入的密码不一致')
      return
    }
    setBusy(true)
    setError('')
    try {
      await resetPassword(token, password)
      navigate('/login', { state: { reset: true } })
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setBusy(false)
    }
  }

  if (!token) {
    return (
      <div className="page">
        <p className="error-text">缺少重置令牌，请从邮件中的链接进入。</p>
        <Link to="/forgot-password">重新发送</Link>
      </div>
    )
  }

  return (
    <div className="page auth-form">
      <h1>重置密码</h1>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="password">新密码</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={6}
            maxLength={64}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="confirm">确认新密码</label>
          <input
            id="confirm"
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            minLength={6}
            maxLength={64}
            required
          />
        </div>
        {error && <p className="error-text">{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? '提交中…' : '重置密码'}
        </button>
      </form>
    </div>
  )
}
