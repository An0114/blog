import { Link, NavLink, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/useAuth'

export function NavBar() {
  const { isLoggedIn, isAdmin, user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <header className="navbar">
      <Link to="/" className="navbar-brand">
        个人博客
      </Link>
      <nav className="navbar-links">
        <NavLink to="/" end>
          动态
        </NavLink>
        {isLoggedIn && (
          <NavLink to="/publish">
            发布
          </NavLink>
        )}
        {isLoggedIn && (
          <NavLink to="/favorites">
            收藏
          </NavLink>
        )}
        {isAdmin && (
          <NavLink to="/admin">
            用户管理
          </NavLink>
        )}
      </nav>
      <div className="navbar-user">
        {isLoggedIn ? (
          <>
            <Link to="/account" className="navbar-username">
              {user?.username}
            </Link>
            <button type="button" className="btn btn-ghost" onClick={handleLogout}>
              退出
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="btn btn-ghost">
              登录
            </Link>
            <Link to="/register" className="btn btn-primary">
              注册
            </Link>
          </>
        )}
      </div>
    </header>
  )
}
