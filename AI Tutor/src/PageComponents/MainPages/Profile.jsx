import React from 'react'
import { useAuth } from '../../ClientStuff/AuthContext.jsx'

export default function Profile() {
    const { userData } = useAuth();

    return (
        <div>
            <h1>Profile Page</h1>
            <p>{userData?.email}</p>
            <p>{userData?.name}</p>
            <p>{userData?.picture_url || "No picture"}</p>
            <p>{userData?.level}</p>
        </div>
    )
}