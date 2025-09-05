import { supabase } from './SupabaseClient'

const API_BASE_URL = import.meta.env.VITE_BACKEND_PORT;

export const callProtectedEndpoint = async () => {
  // Get the current session
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    throw new Error('No active session')
  }

  // Make API call with the access token
  const response = await fetch(`${API_BASE_URL}/protected`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error('API call failed')
  }

  return response.json()
}