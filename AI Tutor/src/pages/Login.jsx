import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx'
import '../PageComponents/CSS/Login.css'

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { signIn } = useAuth();

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);

        console.log(email, password);
    
        const { data, error, action } = await signIn(email, password);
        
        if (!error && data?.user) {  // Check if user exists in data
            alert(`User ${action}! Welcome!`) // "signed_in" or "signed_up"
            navigate('/');
        } else {
            console.log("Authentication failed :(")
            console.log(error?.message || 'Unknown error')
            alert(error?.message || 'Unknown error')
        }
        setLoading(false);
        setEmail('');
        setPassword('');
    }

    return (
        <div className='login_page_full_container'>
            <div className='login_page_container'>
                <h1>Login</h1>
                <form onSubmit={handleLogin}>
                    <input type="email" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
                    <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
                    <button type="submit" disabled={loading}>{loading ? 'Signing in...' : 'Login'}</button>
                </form>
                <div>
                    Don&apos;t have an account? <a href="/signup">Sign up</a>
                </div>
            </div>
            <div className="login_page_graphic">
                some graphic here
            </div>
        </div>
    )
}
