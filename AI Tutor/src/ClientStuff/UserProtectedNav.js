import { useNavigate } from 'react-router-dom'
import { useAuth } from './AuthContext.jsx'

export const useProtectedNavigation = () => {
  const navigate = useNavigate()
  const { session } = useAuth()

  const navigateWithAuth = (targetPath) => {
    if (session) {
      // User is logged in, go to intended destination
      navigate(targetPath)
    } else {
      // User not logged in, redirect to login
      // Optionally store the intended destination
      navigate('/login', { 
        state: { redirectTo: targetPath } // Remember where they wanted to go
      })
    }
  }

  return { navigateWithAuth, isLoggedIn: !!session }
}