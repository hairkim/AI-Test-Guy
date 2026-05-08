import { supabase } from './supabaseClient';
import { getProtectedUser, syncUser } from './userService';

const createOrGetUser = async (authUser) => {
    if (!authUser) return null;

    try {
        return await syncUser({
            id: authUser.id,
            name: authUser.user_metadata?.display_name,
            email: authUser.email,
            createdAt: authUser.created_at,
        });
    } catch (error) {
        console.error('Error syncing user:', error);
        return null;
    }
};

export const signUp = async (email, password, username) => {
    const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
            data: {
                display_name: username,
            },
        },
    });

    const userData = data.user && !error ? await createOrGetUser(data.user) : null;

    return {
        data,
        error,
        action: 'signed up',
        userData,
    };
};

export const signIn = async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
    });

    const userData = data.user && !error ? await createOrGetUser(data.user) : null;

    return {
        data,
        error,
        action: 'signed in',
        userData,
    };
};

export const signOut = async () => {
    try {
        const { error } = await supabase.auth.signOut();

        if (!error) {
            alert('You have been signed out');
        }

        return { error, action: 'signed out' };
    } catch (error) {
        console.error('Sign out failed:', error);
        return { error, action: 'failed to sign out' };
    }
};

export const getSession = () => (
    supabase.auth.getSession()
);

export const callProtectedEndpoint = async () => {
    const { data: { session } } = await supabase.auth.getSession();

    if (!session) {
        throw new Error('No active session');
    }

    return getProtectedUser({ token: session.access_token });
};

export const signInOrSignUp = async (email, password, username) => {
    try {
        const { data: signInData, error: signInError } = await signIn(email, password);

        if (signInData.user && !signInError) {
            return { data: signInData, error: null, action: 'signed_in' };
        }

        if (signInError) {
            const { data: signUpData, error: signUpError } = await signUp(email, password, username || null);

            if (signUpError) {
                return { data: null, error: signUpError, action: 'failed' };
            }

            return { data: signUpData, error: null, action: 'signed_up' };
        }
    } catch (error) {
        return { data: null, error, action: 'failed' };
    }

    return { data: null, error: null, action: 'failed' };
};

export const getUserByEmail = async (email) => {
    try {
        const { data: user, error } = await supabase
            .from('users')
            .select('*')
            .eq('email', email)
            .single();

        if (error && error.code !== 'PGRST116') {
            console.error('Error fetching user by email:', error);
            return null;
        }

        return user;
    } catch (error) {
        console.error('Error fetching user by email:', error);
        return null;
    }
};

export const updateUser = async (userId, updates) => {
    try {
        const { data: updatedUser, error } = await supabase
            .from('users')
            .update(updates)
            .eq('id', userId)
            .select()
            .single();

        if (error) {
            console.error('Error updating user:', error);
            return null;
        }

        return updatedUser;
    } catch (error) {
        console.error('Error updating user:', error);
        return null;
    }
};
