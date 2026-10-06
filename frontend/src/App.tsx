import { Outlet, Route, Routes } from 'react-router-dom'

import { NavBar } from './components/NavBar'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AccountPage } from './pages/AccountPage'
import { AdminPage } from './pages/AdminPage'
import { FavoritesPage } from './pages/FavoritesPage'
import { ForgotPasswordPage } from './pages/ForgotPasswordPage'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { PostDetailPage } from './pages/PostDetailPage'
import { PublishPage } from './pages/PublishPage'
import { RegisterPage } from './pages/RegisterPage'
import { ResetPasswordPage } from './pages/ResetPasswordPage'
import { VerifyEmailPage } from './pages/VerifyEmailPage'

function Layout() {
  return (
    <>
      <NavBar />
      <main className="container">
        <Outlet />
      </main>
    </>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="posts/:id" element={<PostDetailPage />} />
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
          path="publish"
          element={
            <ProtectedRoute>
              <PublishPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin"
          element={
            <ProtectedRoute adminOnly>
              <AdminPage />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  )
}
