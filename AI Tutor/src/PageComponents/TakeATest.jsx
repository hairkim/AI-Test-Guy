import React from 'react'
import './TakeATest.css'
import { useNavigate } from 'react-router-dom'

export default function TakeATest() {
    const navigate = useNavigate();


    return (
        <div className='take-a-test-container'>
            <h1>Take a Test</h1>
            <div className='test-buttons'>
                <button onClick={() => navigate('/math_test')}>Take a Math Test</button>
                <button onClick={() => navigate('/english_test')}>Take an English Test</button>
                <button onClick={() => navigate('/full_exam')}>Take a Full Exam</button>
            </div>
        </div>
    )
}