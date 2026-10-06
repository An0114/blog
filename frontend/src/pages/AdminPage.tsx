import { useEffect, useState } from 'react'

import {
  deleteAdminComment,
  deleteUser,
  listAdminComments,
  listUsers,
  updateUserStatus,
} from '../api/admin'
import { extractErrorDetail } from '../api/client'
import type { AdminCommentOut, User } from '../api/types'
import { formatDateTime } from '../utils/format'

const SIZE = 10

type AdminTab = 'users' | 'comments'

const STATUS_LABEL: Record<User['status'], string> = {
  active: '正常',
  disabled: '已禁用',
  deleted: '已注销',
}

export function AdminPage() {
  const [tab, setTab] = useState<AdminTab>('users')

  return (
    <div className="page">
      <h1>管理页面</h1>
      <div className="filter-bar">
        <button
          type="button"
          className={`btn ${tab === 'users' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setTab('users')}
        >
          用户管理
        </button>
        <button
          type="button"
          className={`btn ${tab === 'comments' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setTab('comments')}
        >
          评论管理
        </button>
      </div>
      {tab === 'users' ? <UserManageTab /> : <CommentManageTab />}
    </div>
  )
}

function UserManageTab() {
  const [users, setUsers] = useState<User[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let ignore = false
    async function fetchUsers() {
      try {
        const data = await listUsers({ page, size: SIZE })
        if (!ignore) {
          setUsers(data.items)
          setTotal(data.total)
        }
      } catch (err) {
        if (!ignore) setError(extractErrorDetail(err))
      }
    }
    void fetchUsers()
    return () => {
      ignore = true
    }
  }, [page])

  const run = async (action: () => Promise<unknown>, successMessage: string) => {
    if (busy) return
    setBusy(true)
    setError('')
    setInfo('')
    try {
      await action()
      setInfo(successMessage)
      const data = await listUsers({ page, size: SIZE })
      setUsers(data.items)
      setTotal(data.total)
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setBusy(false)
    }
  }

  const handleToggle = (user: User) => {
    const nextStatus = user.status === 'active' ? 'disabled' : 'active'
    void run(
      () => updateUserStatus(user.id, nextStatus),
      `已将 ${user.username} ${nextStatus === 'disabled' ? '禁用' : '启用'}`,
    )
  }

  const handleDelete = (user: User) => {
    if (!window.confirm(`确认注销用户「${user.username}」？该用户将无法登录，历史评论保留。`)) {
      return
    }
    void run(() => deleteUser(user.id), `已注销用户 ${user.username}`)
  }

  const totalPages = Math.max(1, Math.ceil(total / SIZE))

  return (
    <>
      {error && <p className="error-text">{error}</p>}
      {info && <p className="success-text">{info}</p>}
      <table className="admin-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>邮箱</th>
            <th>角色</th>
            <th>状态</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.id}</td>
              <td>{user.username}</td>
              <td>{user.email}</td>
              <td>{user.role === 'admin' ? '博主' : '读者'}</td>
              <td>{STATUS_LABEL[user.status]}</td>
              <td>{formatDateTime(user.created_at)}</td>
              <td>
                {user.status === 'deleted' ? (
                  <span className="form-hint">—</span>
                ) : (
                  <>
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      disabled={busy}
                      onClick={() => handleToggle(user)}
                    >
                      {user.status === 'active' ? '禁用' : '启用'}
                    </button>{' '}
                    <button
                      type="button"
                      className="btn btn-danger btn-sm"
                      disabled={busy}
                      onClick={() => handleDelete(user)}
                    >
                      注销
                    </button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="pager">
        <button
          type="button"
          className="btn btn-ghost"
          disabled={page <= 1}
          onClick={() => setPage((p) => p - 1)}
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
          onClick={() => setPage((p) => p + 1)}
        >
          下一页
        </button>
      </div>
    </>
  )
}

function CommentManageTab() {
  const [comments, setComments] = useState<AdminCommentOut[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let ignore = false
    async function fetchComments() {
      try {
        const data = await listAdminComments({ page, size: SIZE })
        if (!ignore) {
          setComments(data.items)
          setTotal(data.total)
        }
      } catch (err) {
        if (!ignore) setError(extractErrorDetail(err))
      }
    }
    void fetchComments()
    return () => {
      ignore = true
    }
  }, [page])

  const handleDelete = async (comment: AdminCommentOut) => {
    if (busy) return
    setBusy(true)
    setError('')
    try {
      await deleteAdminComment(comment.id)
      const data = await listAdminComments({ page, size: SIZE })
      setComments(data.items)
      setTotal(data.total)
    } catch (err) {
      setError(extractErrorDetail(err))
    } finally {
      setBusy(false)
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / SIZE))

  return (
    <>
      {error && <p className="error-text">{error}</p>}
      {comments.length === 0 ? (
        <p className="empty-tip">暂无评论</p>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>动态</th>
              <th>用户</th>
              <th>内容</th>
              <th>时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {comments.map((comment) => (
              <tr key={comment.id}>
                <td>{comment.id}</td>
                <td>{comment.post_title}</td>
                <td>{comment.username}</td>
                <td>{comment.content}</td>
                <td>{formatDateTime(comment.created_at)}</td>
                <td>
                  <button
                    type="button"
                    className="btn btn-danger btn-sm"
                    disabled={busy}
                    onClick={() => void handleDelete(comment)}
                  >
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div className="pager">
        <button
          type="button"
          className="btn btn-ghost"
          disabled={page <= 1}
          onClick={() => setPage((p) => p - 1)}
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
          onClick={() => setPage((p) => p + 1)}
        >
          下一页
        </button>
      </div>
    </>
  )
}
