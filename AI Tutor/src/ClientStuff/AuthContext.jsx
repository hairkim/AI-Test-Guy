import React, { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from './SupabaseClient'
import { signIn, signUp, signOut, getSession } from './auth.js'
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
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  const value = {
    session,
    user: session?.user || null,
    loading,
    signIn,
    signUp,
    signOut,
  }

  console.log('🎯 AuthContext providing:', { session: !!session, user: !!session?.user, loading })

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

AuthProvider.propTypes = {
    children: PropTypes.node.isRequired,
}