import React from 'react'
import { useAuth } from '../ClientStuff/AuthContext.jsx'

export default function Profile() {
    const { user } = useAuth();

    return (
        <div>
            <h1>Profile Page</h1>
            <p>{user?.email}</p>
            <p>{user?.user_metadata?.display_name}</p>
        </div>
    )
}