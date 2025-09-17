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
    
    getSession().then(({ data: { session } }) => {
      setSession(session)
      setLoading(false)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        console.log('🔄 Auth state changed:', event)
        console.log('📋 New session:', session)
        setSession(session)

        if(event === "SIGNED_OUT") {
            setUserData(null)
        } else if (event === "SIGNED_IN" || event === "TOKEN_REFRESHED") {
          fetchUserData(session.user)
        }
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [])
  const value = {
    session,
    user: session?.user || null,
    userData,
    loading,
    signIn,
    signUp,
    signOut,
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