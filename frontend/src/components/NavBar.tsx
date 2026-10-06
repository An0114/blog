import { Link, NavLink, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/useAuth'
import { SiteLogo } from './SiteLogo'

/**
 * 深色侧边导航栏（主题：未完成的页）。
 * 栏目可见性：动态/发布/收藏/草稿箱/用户管理 + 关于我（位于导航最后，见单元 3）。
 */
export function NavBar() {
  const { isLoggedIn, isAdmin, user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/home')
  }

  return (
    <aside className="sidebar">
      <Link to="/home" className="sidebar-brand">
        <SiteLogo size={40} />
        <span>未完成的页</span>
      </Link>
      <p className="sidebar-tagline">这里只放我真正在乎的文字</p>
      <nav className="sidebar-nav">
        <NavLink to="/home" end>
          动态
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
        {/* 关于我：所有用户导航的最后一个标签（PRD A15） */}
        <NavLink to="/about">
          关于我
        </NavLink>
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
