import { useState } from 'react'
import { Link } from 'react-router-dom'

import { forgotPassword } from '../api/auth'
import { extractErrorDetail } from '../api/client'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [info, setInfo] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (busy) return
    setBusy(true)
    setError('')
    setInfo('')
    try {
      const res = await forgotPassword(email.trim())
      setInfo(`${res.message}（本地模式重置链接见后端日志）`)
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page auth-form">
      <h1>找回密码</h1>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="email">注册邮箱</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        {info && <p className="success-text">{info}</p>}
        {error && <p className="error-text">{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? '发送中…' : '发送重置链接'}
        </button>
        <p className="form-hint">
          <Link to="/login">返回登录</Link>
        </p>
      </form>
    </div>
  )
}
