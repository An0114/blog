import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { confirmVerifyEmail } from '../api/auth'
import { extractErrorDetail } from '../api/client'
import { useAuth } from '../context/useAuth'

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''
  const { updateUser } = useAuth()
  const [state, setState] = useState<'loading' | 'ok' | 'fail'>('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    async function run() {
      try {
        const updated = await confirmVerifyEmail(token)
        if (!ignore) {
          updateUser(updated)
          setState('ok')
        }
      } catch (err) {
        if (!ignore) {
          setState('fail')
          setError(extractErrorDetail(err))
        }
      }
    }
    void run()
    return () => {
      ignore = true
    }
  }, [token, updateUser])

  if (state === 'loading') return <p className="empty-tip">正在验证邮箱…</p>

  return (
    <div className="page">
      <h1>邮箱验证</h1>
      {state === 'ok' ? (
        <>
          <p className="success-text">验证成功！</p>
          <Link to="/account">返回账户设置</Link>
        </>
      ) : (
        <>
          <p className="error-text">{error || '验证失败'}</p>
          <Link to="/account">返回账户设置重试</Link>
        </>
      )}
    </div>
  )
}
