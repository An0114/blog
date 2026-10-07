import { Suspense, lazy } from 'react'
import { Outlet, Route, Routes } from 'react-router-dom'

import { AdminRoute } from './components/AdminRoute'
import { NavBar } from './components/NavBar'
import { ProtectedRoute } from './components/ProtectedRoute'
// 首屏与部署关键页保持 eager：着陆页（第一屏）与初始化页（部署场景）不参与代码分割
import { InitPage } from './pages/InitPage'
import { LandingPage } from './pages/LandingPage'

// 其余页面路由级代码分割（React.lazy）：按需加载 chunk，减小首屏 bundle
const AboutPage = lazy(() => import('./pages/AboutPage').then((m) => ({ default: m.AboutPage })))
const AccountPage = lazy(() => import('./pages/AccountPage').then((m) => ({ default: m.AccountPage })))
const AdminPage = lazy(() => import('./pages/AdminPage').then((m) => ({ default: m.AdminPage })))
const DraftsPage = lazy(() => import('./pages/DraftsPage').then((m) => ({ default: m.DraftsPage })))
const FavoritesPage = lazy(() =>
  import('./pages/FavoritesPage').then((m) => ({ default: m.FavoritesPage })),
)
const ForgotPasswordPage = lazy(() =>
  import('./pages/ForgotPasswordPage').then((m) => ({ default: m.ForgotPasswordPage })),
)
const HomePage = lazy(() => import('./pages/HomePage').then((m) => ({ default: m.HomePage })))
const LoginPage = lazy(() => import('./pages/LoginPage').then((m) => ({ default: m.LoginPage })))
const PostDetailPage = lazy(() =>
  import('./pages/PostDetailPage').then((m) => ({ default: m.PostDetailPage })),
)
const PublishPage = lazy(() => import('./pages/PublishPage').then((m) => ({ default: m.PublishPage })))
const RegisterPage = lazy(() =>
  import('./pages/RegisterPage').then((m) => ({ default: m.RegisterPage })),
)
const ResetPasswordPage = lazy(() =>
  import('./pages/ResetPasswordPage').then((m) => ({ default: m.ResetPasswordPage })),
)
const VerifyEmailPage = lazy(() =>
  import('./pages/VerifyEmailPage').then((m) => ({ default: m.VerifyEmailPage })),
)

function Layout() {
  return (
    <div className="layout">
      <NavBar />
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}

function PageFallback() {
  return <p className="empty-tip">加载中…</p>
}

export default function App() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        {/* 着陆页：站点第一个页面（无侧栏，全屏） */}
        <Route path="/" element={<LandingPage />} />
        {/* 站点初始化：仅未初始化时开放（无侧栏，独立全屏） */}
        <Route path="/admin/init" element={<InitPage />} />
        <Route element={<Layout />}>
          <Route path="home" element={<HomePage />} />
          <Route path="posts/:id" element={<PostDetailPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
          <Route path="forgot-password" element={<ForgotPasswordPage />} />
          <Route path="reset-password" element={<ResetPasswordPage />} />
          <Route path="verify-email" element={<VerifyEmailPage />} />
          <Route
            path="account"
            element={
              <ProtectedRoute>
                <AccountPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="favorites"
            element={
              <ProtectedRoute>
                <FavoritesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="drafts"
            element={
              <AdminRoute>
                <DraftsPage />
              </AdminRoute>
            }
          />
          <Route
            path="publish"
            element={
              <AdminRoute>
                <PublishPage />
              </AdminRoute>
            }
          />
          <Route
            path="admin"
            element={
              <AdminRoute>
                <AdminPage />
              </AdminRoute>
            }
          />
        </Route>
      </Routes>
    </Suspense>
  )
}
