// Page design layout:
// A. Main page (this page) will begin with a "Start Test" button
// B. Once the user clicks "Start Test", the page will display the first question
//    - all questions must be loaded from the database
//    - all questions are going to be separate components (maybe like Sat question component or something)
//    - the timer will start and the user will be given a certain amount of time that is tracked in react
// C. When the user is done with the questions, the page will:
//    - display results
//    - show a "Retake Test" button
//    - some more stuff i need to think about

import React, { useState } from 'react'
import './MathPage.css'
import AppHeader from './AppHeader.jsx'
import SatQuestion from './SatQuestion.jsx'


export default function MathTestPage() {
    const [questions, setQuestions] = useState([])
    const [testState, setTestState] = useState("idle")
    const [currentIndex, setCurrentIndex] = useState(0)
    const [userAnswer, setUserAnswer] = useState({})

    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;

    const startTest = async () => {
        setTestState("loading")
        try {
            const response = await fetch(`${BACKEND_URL}/api/sat/mock-exam/generate`, {
                method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                exam_type: 'math_only'
            })
        })
            const data = await response.json()
            setQuestions(data.questions)
            console.log("fetching worked, showing some questions: " + data.questions[0].question_text)
            setTestState("active")
        } catch (error) {
            console.error("Error loading questions:", error)
            setTestState("error")
        }
    }

    const selectNextQuestion = () => {
        if (currentIndex === questions.length - 1) {
            return
        }
        setCurrentIndex(currentIndex + 1)
    }

    const selectPreviousQuestion = () => {
        if (currentIndex === 0) {
            return
        }
        setCurrentIndex(currentIndex - 1)
    }

    const handleAnswerSelect = (questionId, answer) => {
        console.log("Question ID:", questionId)
        console.log("Selected Answer:", answer)
        setUserAnswer(prev => ({
            ...prev,
            [questionId]: answer
        }))
    }


    return (
        <div className='main_container'>
            <AppHeader />
            {testState === 'idle' && (
                <div className="start_page">
                    <h1>Math Test Page</h1>
                    <button onClick={startTest} disabled={testState === 'loading'}>
                        {testState === 'idle' ? 'Start Test' 
                        : testState === 'loading' ? 'Loading...' 
                        : 'Error'}
                    </button>
                </div>
            )}
            {testState === 'active' && (
                <div className="test_page">
                    <SatQuestion key={questions[currentIndex].id} question={questions[currentIndex]} index={currentIndex + 1} selectedAnswer={userAnswer[questions[currentIndex].id]} handleAnswerSelect={(questionId, answer) => handleAnswerSelect(questionId, answer)} />
                    <div className="button_container">
                        <button onClick={() => selectPreviousQuestion()}>Previous</button>
                        <button onClick={() => selectNextQuestion()}>Next</button>
                    </div>
                </div>
            )}
        </div>
    )
}
