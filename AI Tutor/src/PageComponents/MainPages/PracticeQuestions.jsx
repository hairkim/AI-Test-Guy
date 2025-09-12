import React, { useState } from 'react'
import SatQuestion from '../SupportingComponents/SatQuestion.jsx'
import { useLocation } from 'react-router-dom'
import '../CSS/PracticeQuestions.css'

export default function PracticeQuestions() {
    const location = useLocation()
    const {questions} = location.state || {}
    const [currentIndex, setCurrentIndex] = useState(0)
    const [userAnswer, setUserAnswer] = useState({})

    const handleAnswerSelect = (questionId, answer) => {
        setUserAnswer({
            ...userAnswer,
            [questionId]: answer
        })
    }

    const handleNextQuestion = () => {
        setCurrentIndex(currentIndex + 1)
    }

    const handlePreviousQuestion = () => {
        setCurrentIndex(currentIndex - 1)
    }

    // const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;

    return (
        <div>
            {questions && (
                <div className='practice_question_container'>
                    <div className='question_container'>
                        <SatQuestion key={questions[currentIndex].id} question={questions[currentIndex]} index={currentIndex + 1} selectedAnswer={userAnswer[questions[currentIndex].id]} handleAnswerSelect={(questionId, answer) => handleAnswerSelect(questionId, answer)} />
                        <div className="practice-question-buttons">
                            <button onClick={handlePreviousQuestion} disabled={currentIndex === 0}>Previous</button>
                            <button onClick={handleNextQuestion} disabled={currentIndex === questions.length - 1}>Next</button>
                        </div>
                    </div>
                    <div className='ai_container'>
                        <h2>AI Tutor</h2>
                    </div>
                </div>
            )}
        </div>
    )
}
