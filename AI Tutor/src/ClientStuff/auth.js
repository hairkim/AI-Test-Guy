import { supabase } from './SupabaseClient'

// Sign up
export const signUp = async (email, password, username) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
        data: {
          display_name: username,
          // You can add more fields
          avatar_url: '',
          website: '',
        }
      }
  })
  return { data, error, action: "signed up" }
}

// Sign in
export const signIn = async (email, password) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  return { data, error, action: "signed in" }
}

// Sign out
export const signOut = async () => {
  const { error } = await supabase.auth.signOut()

  if (!error) {
    alert('You have been signed out')
  }
  return { error }
}

// Get current session
export const getSession = () => {
  return supabase.auth.getSession()
}

export const signInOrSignUp = async (email, password, username) => {
    try {
      // First, try to sign in
      const { data: signInData, error: signInError } = await signIn(email, password)
  
      if (signInData.user && !signInError) {
        return { data: signInData, error: null, action: 'signed_in' }
      }
  
      // If sign in failed, try to sign up
      if (signInError) {
        const { data: signUpData, error: signUpError } = await signUp(email, password, username || null)
  
        if (signUpError) {
          return { data: null, error: signUpError, action: 'failed' }
        }
  
        return { data: signUpData, error: null, action: 'signed_up' }
      }
  
    } catch (error) {
      return { data: null, error, action: 'failed' }
    }
  }