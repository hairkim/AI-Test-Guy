import React, { createContext, useContext, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { supabase } from '../services/supabaseClient';
import {
    getSession,
    getUserByEmail,
    signIn,
    signOut,
    signUp,
    updateUser,
} from '../services/authService';

const AuthContext = createContext({});

export const useAuth = () => {
    const context = useContext(AuthContext);

    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }

    return context;
};

export const AuthProvider = ({ children }) => {
    const [session, setSession] = useState(null);
    const [loading, setLoading] = useState(true);
    const [userData, setUserData] = useState(null);

    const fetchUserData = async (authUser) => {
        if (!authUser?.email) {
            setUserData(null);
            return null;
        }

        try {
            const user = await getUserByEmail(authUser.email);
            setUserData(user);
            return user;
        } catch (error) {
            console.error('Error fetching user data:', error);
            setUserData(null);
            return null;
        }
    };

    const updateUserData = async (updates) => {
        if (!userData?.id) return null;

        try {
            const updatedUser = await updateUser(userData.id, updates);

            if (updatedUser) {
                setUserData(updatedUser);
            }

            return updatedUser;
        } catch (error) {
            console.error('Error updating user data:', error);
            return null;
        }
    };

    useEffect(() => {
        getSession().then(({ data: { session: currentSession } }) => {
            setSession(currentSession);
            setLoading(false);

            if (currentSession?.user) {
                fetchUserData(currentSession.user);
            }
        });

        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            (event, nextSession) => {
                setSession(nextSession);

                if (event === 'SIGNED_OUT') {
                    setUserData(null);
                } else if (nextSession?.user && (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED')) {
                    fetchUserData(nextSession.user);
                }

                setLoading(false);
            }
        );

        return () => subscription.unsubscribe();
    }, []);

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
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

AuthProvider.propTypes = {
    children: PropTypes.node.isRequired,
};
