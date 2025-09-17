import { supabase } from './SupabaseClient'

const createOrGetUser = async (authUser) => {
  if (!authUser) return null

  try {
    // First, try to get existing user by email
    const { data: existingUser, error: fetchError } = await supabase
      .from('users')
      .select('*')
      .eq('email', authUser.email)
      .single()

    if (existingUser && !fetchError) {
      console.log('✅ Found existing user:', existingUser)
      return existingUser
    }

    // If user doesn't exist (PGRST116 = no rows returned), create them
    if (fetchError?.code === 'PGRST116') {
      console.log('👤 Creating new user in users table...')
      
      const { data: newUser, error: insertError } = await supabase
        .from('users')
        .insert({
          name: authUser.user_metadata?.display_name || authUser.email.split('@')[0],
          email: authUser.email,
          picture_url: authUser.user_metadata?.avatar_url || null,
          level: 1 // Default level
        })
        .select()
        .single()

      if (newUser && !insertError) {
        console.log('✅ Created new user:', newUser)
        return newUser
      } else {
        console.error('❌ Error creating user:', insertError)
        return null
      }
    } else {
      console.error('❌ Error fetching user:', fetchError)
      return null
    }
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