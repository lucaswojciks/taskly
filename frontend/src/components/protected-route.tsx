import { Navigate, Outlet } from 'react-router-dom'
import { getToken } from '@/lib/auth'

/**
 * Guards nested routes: with no token in localStorage the user is redirected to
 * /login (replacing history so Back doesn't loop).
 */
export function ProtectedRoute() {
  if (getToken() === null) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}
