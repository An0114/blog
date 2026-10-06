import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { register } from '../api/auth'
import { extractErrorDetail } from '../api/client'

export function RegisterPage() {
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
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
      await register({ username: username.trim(), email: email.trim(), password })
      navigate('/login', { state: { registered: true } })
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page auth-form">
      <h1>注册</h1>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="username">用户名</label>
          <input
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            minLength={2}
            maxLength={50}
            required
          />
        </div>
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
            minLength={6}
            required
          />
        </div>
        {error && <p className="error-text">{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? '注册中…' : '注册'}
        </button>
        <p className="form-hint">
          已有账号？<Link to="/login">去登录</Link>
        </p>
      </form>
    </div>
  )
}
