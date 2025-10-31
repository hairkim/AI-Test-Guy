import React, { useEffect } from 'react';
import { supabase } from '../SupabaseClient';

const Signout = () => {
    useEffect(() => {
        const { error } = supabase.auth.signOut();
        if (error) {
            console.error('Error signing out:', error);
        }
    }, []);

    return (
        <div>
            <h1>Signing out...</h1>
        </div>
    );
};

export default Signout;
