import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom';
import { signUp } from '../../ClientStuff/auth';
import '../CSS/Login.css'

export default function Signup() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [username, setUsername] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSignup = async (e) => {
        e.preventDefault();
        setLoading(true);

        console.log(email, password, username.trim());
    
        const { data, error, action } = await signUp(email, password, username.trim());
        
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
        setUsername('');
    }

    return (
        <div className='login_page_full_container'>
            <div className='login_page_container'>
                <h1>Sign Up</h1>
                <form onSubmit={handleSignup}>
                    <input type="email" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
                    <input type="text" placeholder="Username" onChange={(e) => setUsername(e.target.value)} />
                    <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
                    <button type="submit" disabled={loading}>{loading ? 'Signing up...' : 'Sign Up'}</button>
                </form>
                <div>
                    Already have an account? <a href="/login">Login</a>
                </div>
            </div>
            <div className="login_page_graphic">
                some graphic here
            </div>
        </div>
    )
}