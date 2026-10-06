import { Link, NavLink, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/useAuth'

/**
 * 深色侧边导航栏（主题：未完成的页）。
 * 栏目可见性：动态/发布/收藏/草稿箱/用户管理 + 关于我（见单元 30 权限矩阵）。
 */
export function NavBar() {
  const { isLoggedIn, isAdmin, user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <aside className="sidebar">
      <Link to="/" className="sidebar-brand">
        未完成的页
      </Link>
      <p className="sidebar-tagline">这里只放我真正在乎的文字</p>
      <nav className="sidebar-nav">
        <NavLink to="/" end>
          动态
        </NavLink>
        <NavLink to="/about">
          关于我
        </NavLink>
        {isLoggedIn && (
          <NavLink to="/favorites">
            收藏
          </NavLink>
        )}
        {isAdmin && (
          <NavLink to="/publish">
            发布
          </NavLink>
        )}
        {isAdmin && (
          <NavLink to="/drafts">
            草稿箱
          </NavLink>
        )}
        {isAdmin && (
          <NavLink to="/admin">
            用户管理
          </NavLink>
        )}
      </nav>
      <div className="sidebar-user">
        {isLoggedIn ? (
          <>
            <Link to="/account" className="sidebar-username">
              {user?.username}
            </Link>
            <button type="button" className="btn btn-ghost btn-sm" onClick={handleLogout}>
              退出
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="btn btn-ghost btn-sm">
              登录
            </Link>
            <Link to="/register" className="btn btn-primary btn-sm">
              注册
            </Link>
          </>
        )}
      </div>
    </aside>
  )
}
