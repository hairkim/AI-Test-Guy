import { supabase } from './SupabaseClient'
import { syncUser } from '../services/userService'

const createOrGetUser = async (authUser) => {
  if (!authUser) return null
  console.log("authUser: ", authUser)

  try {
    const userData = await syncUser({
      id: authUser.id,
      name: authUser.user_metadata?.display_name,
      email: authUser.email,
      createdAt: authUser.created_at,
    })

    console.log('✅ User synced:', userData)
    return userData

  } catch (error) {
    console.error('❌ Error in createOrGetUser:', error)
    return null
  }
}

// Sign up
export const signUp = async (email, password, username) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
        data: {
          display_name: username
        }
      }
  })
  let userData = null
  if (data.user && !error) {
    userData = await createOrGetUser(data.user)
  }

  return { 
    data, 
    error, 
    action: "signed up",
    userData // Include custom user data
  }
}

// Sign in
export const signIn = async (email, password) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  let userData = null
  if (data.user && !error) {
    userData = await createOrGetUser(data.user)
  }

  return { 
    data, 
    error, 
    action: "signed in",
    userData // Include custom user data
  }
}

// Sign out
export const signOut = async () => {
  console.log('reached signout function in auth.js')
  
  try {
    const { error } = await supabase.auth.signOut()
    
    if (!error) {
      alert('You have been signed out')
    }
    return { error, action: "signed out" }
    
  } catch (err) {
    console.error('SignOut exception:', err)
    return { error: err, action: "failed to sign out" }
  }
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

export const getUserByEmail = async (email) => {
  try {
    const { data: user, error } = await supabase
      .from('users')
      .select('*')
      .eq('email', email)
      .single()

    if (error && error.code !== 'PGRST116') {
      console.error('Error fetching user by email:', error)
      return null
    }

    return user
  } catch (error) {
    console.error('Error in getUserByEmail:', error)
    return null
  }
}

// New helper function to update user data
export const updateUser = async (userId, updates) => {
  try {
    const { data: updatedUser, error } = await supabase
      .from('users')
      .update(updates)
      .eq('id', userId)
      .select()
      .single()

    if (error) {
      console.error('Error updating user:', error)
      return null
    }

    return updatedUser
  } catch (error) {
    console.error('Error in updateUser:', error)
    return null
  }
}
