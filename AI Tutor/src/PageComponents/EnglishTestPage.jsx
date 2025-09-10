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
import { useAuth } from '../ClientStuff/AuthContext.jsx';


export default function EnglishTestPage() {
    const { user } = useAuth();
    const [questions, setQuestions] = useState([])
    const [testState, setTestState] = useState("idle")
    const [currentIndex, setCurrentIndex] = useState(0)
    const [userAnswer, setUserAnswer] = useState({})
    const [module, setModule] = useState(1)
    const [examId, setExamId] = useState(null)
    const [score, setScore] = useState(null)
    const [percentage, setPercentage] = useState(null)

    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;

    const startTest = async () => {
        setTestState("loading")
        setUserAnswer({})
        try {
            const response = await fetch(`${BACKEND_URL}/api/sat/mock-exam/generate`, {
                method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                exam_type: 'english_only',
                user_id: user.id
            })
        })
            const data = await response.json()
            setQuestions(data.questions)
            setExamId(data.exam_id)
            setModule(1)
            setCurrentIndex(0)
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

    const submitTest = async() => {
        if (!examId) {
            console.error("No exam ID found")
            return
        }
        console.log("submitting test")
        setTestState("loading")
        
        try {
            const response = await fetch(`${BACKEND_URL}/api/sat/submit_test/${module}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    exam_id: examId,
                    answers: userAnswer,
                    module: module
                })
            })

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json()
            console.log("Submit response:", data)

            if (module === 1) {
                // Module 1 completed - load module 2
                setQuestions(data.module2_questions) // Load module 2 questions
                setModule(2)
                setCurrentIndex(0)
                setUserAnswer({}) // Reset answers for module 2
                setTestState("module2_active")
            } else {
                // Module 2 completed - show final results
                setScore(data.score)
                setPercentage(data.percentage)
                setTestState("completed")
            }

        } catch (error) {
            console.error("Error submitting test:", error)
            setTestState("error")
        }
    }


    return (
        <div className='main_container'>
            {testState === 'idle' && (
                <div className="start_page">
                    <h1>English Test Page</h1>
                    <div className='start_button'>
                        <button onClick={startTest} disabled={testState === 'loading'}>
                            {testState === 'idle' ? 'Start Test' 
                            : testState === 'loading' ? 'Loading...' 
                            : 'Error'}
                        </button>
                        <div className='test-info'>
                            <h2>You are about to take a practice english only exam</h2>
                            <p>The test includes 2 modules, each with 27 questions</p>
                            <p>You will be given module 2 questions based on previous scoring</p>
                            <p>There is no penalty for wrong answers</p>
                            <p>Good luck!</p>
                        </div>
                    </div>
                </div>
            )}
            {(testState === 'active' || testState === 'module2_active') && (
                <div className="test_page">
                    <SatQuestion key={questions[currentIndex].id} question={questions[currentIndex]} index={currentIndex + 1} selectedAnswer={userAnswer[questions[currentIndex].id]} handleAnswerSelect={(questionId, answer) => handleAnswerSelect(questionId, answer)} />
                    <div className="button_container">
                        <button onClick={() => selectPreviousQuestion()}>Previous</button>
                        <button onClick={() => selectNextQuestion()}>Next</button>
                    </div>
                    <div className='submit_container'>
                        <button onClick={submitTest}>Submit</button>
                    </div>   
                </div>
            )}
            {(testState === 'completed' && score !== null && percentage !== null) && (
                <div className="results_page">
                    <h1>Test Results</h1>
                    <p>Score: {score}</p>
                    <p>Percentage: {percentage}</p>
                    <button onClick={startTest}>Retake Test</button>
                </div>
            )}
        </div>
    )
}
