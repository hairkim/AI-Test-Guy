import { supabase } from './SupabaseClient'
import { getProtectedUser } from '../services/userService'

export const callProtectedEndpoint = async () => {
  // Get the current session
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    throw new Error('No active session')
  }

  return getProtectedUser({ token: session.access_token })
}
