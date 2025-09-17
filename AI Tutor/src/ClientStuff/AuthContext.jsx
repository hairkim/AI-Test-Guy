import React, { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from './SupabaseClient'
import { signIn, signUp, signOut, getSession, getUserByEmail, updateUser } from './auth.js'
import PropTypes from 'prop-types'

const AuthContext = createContext({})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [userData, setUserData] = useState(null)


  const fetchUserData = async (authUser) => {
    if (!authUser?.email) {
      setUserData(null)
      return null
    }

    try {
      const user = await getUserByEmail(authUser.email)
      setUserData(user)
      return user
    } catch (error) {
      console.error('Error fetching user data:', error)
      setUserData(null)
      return null
    }
  }

  // Enhanced signIn wrapper
  const handleSignIn = async (email, password) => {
    const result = await signIn(email, password)
    
    if (result.userData) {
      setUserData(result.userData)
    }
    
    return result
  }

  // Enhanced signUp wrapper
  const handleSignUp = async (email, password, username) => {
    const result = await signUp(email, password, username)
    
    if (result.userData) {
      setUserData(result.userData)
    }
    
    return result
  }

  // Enhanced signOut wrapper
  const handleSignOut = async () => {
    const result = await signOut()
    
    if (!result.error) {
      setUserData(null)
    }
    
    return result
  }

  // Function to update user data
  const updateUserData = async (updates) => {
    if (!userData?.id) return null

    try {
      const updatedUser = await updateUser(userData.id, updates)
      
      if (updatedUser) {
        setUserData(updatedUser)
      }
      
      return updatedUser
    } catch (error) {
      console.error('Error updating user data:', error)
      return null
    }
  }

  useEffect(() => {
    // Get initial session
    getSession().then(async ({ data: { session } }) => {
      console.log('🔍 Initial session check:', session)
      setSession(session)
      
      if (session?.user) {
        // Fetch user data when session exists
        await fetchUserData(session.user)
      }
      
      setLoading(false)
    })

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('🔄 Auth state changed:', event)
        console.log('📋 New session:', session)
        
        setSession(session)
        
        if (session?.user) {
          // Handle sign in/up - fetch user data
          if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
            await fetchUserData(session.user)
          }
        } else {
          // Handle sign out
          if (event === 'SIGNED_OUT') {
            setUserData(null)
          }
        }
        
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  const value = {
    session,
    user: session?.user || null, // Supabase auth user
    userData, // Your custom user data
    loading,
    signIn: handleSignIn,
    signUp: handleSignUp,
    signOut: handleSignOut,
    updateUserData,
    fetchUserData,
  }

  console.log('🎯 AuthContext providing:', { 
    session: !!session, 
    user: !!session?.user, 
    userData: !!userData,
    userEmail: session?.user?.email,
    loading 
  })

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

AuthProvider.propTypes = {
    children: PropTypes.node.isRequired,
}