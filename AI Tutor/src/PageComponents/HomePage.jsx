import React from 'react';
import AppHeader from './AppHeader.jsx'
import './HomePage.css'
import { useAuth } from '../ClientStuff/AuthContext.jsx'
import { useProtectedNavigation } from '../ClientStuff/UserProtectedNav.js'

export default function HomePage() {
    const { navigateWithAuth } = useProtectedNavigation()
    const { user } = useAuth();

    return (
        <div className="home-page">
            <AppHeader />
            {user && (
                <h1>Welcome {user?.user_metadata?.display_name}</h1>
            )}
            <div className="button-container">
                <button onClick={() => navigateWithAuth('/math_test')}>Take a Math Test</button>
                <button onClick={() => navigateWithAuth('/english_test')}>Take an English Test</button>
            </div>
        </div>
    )
}