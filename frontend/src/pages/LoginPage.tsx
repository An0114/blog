import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { login } from '../api/auth'
import { extractErrorDetail } from '../api/client'
import { useAuth } from '../context/useAuth'

export function LoginPage() {
  const { login: saveSession } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as { registered?: boolean; reset?: boolean } | null
  const registered = state?.registered === true
  const reset = state?.reset === true

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (submitting) return
    setSubmitting(true)
    setError('')
    try {
      const { token, user } = await login({ email: email.trim(), password })
      saveSession(token, user)
      navigate('/home')
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page auth-form">
      <h1>登录</h1>
      {registered && <p className="success-text">注册成功，请登录。</p>}
      {reset && <p className="success-text">密码已重置，请使用新密码登录。</p>}
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="email">邮箱</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="password">密码</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <p className="error-text">{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? '登录中…' : '登录'}
        </button>
        <p className="form-hint">
          还没有账号？<Link to="/register">注册</Link>
          {' · '}
          <Link to="/forgot-password">忘记密码</Link>
        </p>
      </form>
    </div>
  )
}
