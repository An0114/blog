import { useState } from 'react'

import { confirmVerifyEmail, requestVerifyEmail } from '../api/auth'
import { extractErrorDetail } from '../api/client'
import { useAuth } from '../context/useAuth'

export function AccountPage() {
  const { user, updateUser } = useAuth()
  const [info, setInfo] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [tokenInput, setTokenInput] = useState('')

  if (!user) return <p className="empty-tip">请先登录</p>

  const handleSend = async () => {
    if (busy) return
    setBusy(true)
    setError('')
    setInfo('')
    try {
      const res = await requestVerifyEmail()
      setInfo(`${res.message}（${res.expires_minutes} 分钟内有效）`)
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setBusy(false)
    }
  }

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = tokenInput.trim()
    if (!token || busy) return
    setBusy(true)
    setError('')
    setInfo('')
    try {
      const updated = await confirmVerifyEmail(token)
      updateUser(updated)
      setInfo('邮箱验证成功')
      setTokenInput('')
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page">
      <h1>账户设置</h1>
      <table className="admin-table">
        <tbody>
          <tr>
            <th>用户名</th>
            <td>{user.username}</td>
          </tr>
          <tr>
            <th>邮箱</th>
            <td>{user.email}</td>
          </tr>
          <tr>
            <th>邮箱验证</th>
            <td>
              {user.email_verified ? (
                <span className="success-text">已验证</span>
              ) : (
                <>
                  <span className="error-text">未验证</span>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    style={{ marginLeft: 8 }}
                    disabled={busy}
                    onClick={() => void handleSend()}
                  >
                    发送验证邮件
                  </button>
                </>
              )}
            </td>
          </tr>
        </tbody>
      </table>

      {!user.email_verified && (
        <form className="comment-form" onSubmit={handleConfirm}>
          <input
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            placeholder="粘贴邮件链接中的 token（本地模式见后端日志）"
          />
          <button type="submit" className="btn btn-primary" disabled={busy || !tokenInput.trim()}>
            确认验证
          </button>
        </form>
      )}

      {info && <p className="success-text">{info}</p>}
      {error && <p className="error-text">{error}</p>}
    </div>
  )
}
