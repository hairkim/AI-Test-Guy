import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom';
import { signIn, signUp } from '../ClientStuff/auth';

export default function Login() {
    const [page, setPage] = useState("login")
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [username, setUsername] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

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
        <>
            <button onClick={() => setPage("login")}>Login</button>
            <button onClick={() => setPage("signup")}>Sign Up</button>
            {page === "login" ? (
                <div>
                    <h1>Login</h1>
                    <form onSubmit={handleLogin}>
                        <input type="email" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
                        <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
                        <button type="submit" disabled={loading}>{loading ? 'Signing in...' : 'Login'}</button>
                    </form>
                </div>
            ) : page === "signup" ? (
                <div>
                    <h1>Sign Up</h1>
                    <form onSubmit={handleSignup}>
                        <input type="email" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
                        <input type="text" placeholder="Username" onChange={(e) => setUsername(e.target.value)} />
                        <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
                        <button type="submit" disabled={loading}>{loading ? 'Signing up...' : 'Sign Up'}</button>
                    </form>
                </div>
            ) : null}
        </>
    )
}