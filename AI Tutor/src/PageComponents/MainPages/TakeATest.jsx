import React from 'react'
import '../CSS/TakeATest.css'
import { useNavigate } from 'react-router-dom'

export default function TakeATest() {
    const navigate = useNavigate();


    return (
        <div className='take-a-test-container'>
            <h1>Take a Test</h1>
            <div className='test-buttons'>
                <button onClick={() => navigate('/test/math_only')}>Take a Math Test</button>
                <button onClick={() => navigate('/test/english_only')}>Take an English Test</button>
                <button onClick={() => navigate('/full_exam')}>Take a Full Exam</button>
            </div>
        </div>
    )
}