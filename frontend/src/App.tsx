import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '@/components/protected-route'
import { DashboardPage } from '@/pages/dashboard'
import { LoginPage } from '@/pages/login'
import { RegisterPage } from '@/pages/register'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<DashboardPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
