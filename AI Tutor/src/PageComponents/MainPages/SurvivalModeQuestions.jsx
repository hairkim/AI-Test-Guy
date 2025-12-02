import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import SurvivalQuestion from '../SupportingComponents/SurvivalQuestion'
import '../CSS/SurvivalModeQuestions.css'
import { useAuth } from '../../ClientStuff/AuthContext'
import GameOver from '../SupportingComponents/GameOver'

export default function SurvivalModeQuestions() {
    const location = useLocation()
    const navigate = useNavigate()
    const { user } = useAuth()
    
    // Get section and difficulty from navigation state
    const { section, difficulty } = location.state || {}
    
    // Game state
    const [lives, setLives] = useState(3)
    const [currentQuestion, setCurrentQuestion] = useState(null)
    const [excludedQuestionIds, setExcludedQuestionIds] = useState([])
    const [selectedAnswer, setSelectedAnswer] = useState(null)
    const [showFeedback, setShowFeedback] = useState(false)
    const [loading, setLoading] = useState(false)
    const [gameOver, setGameOver] = useState(false)
    const [startingTime, setStartingTime] = useState(null)
    
    // Stats for saving session
    const [questionsAnswered, setQuestionsAnswered] = useState(0)
    const [questionsCorrect, setQuestionsCorrect] = useState(0)
    const [answers, setAnswers] = useState([])

    const BACKEND_URL = import.meta.env.VITE_BACKEND_PORT

    // Redirect if no section/difficulty provided
    useEffect(() => {
        if (!section || !difficulty) {
            navigate('/survival', { replace: true })
            return
        }
        startSurvivalMode()
        // Load first question
        fetchQuestion()
    }, [])

    const startSurvivalMode = () => {
        setStartingTime(new Date().toISOString())
    }

    const fetchQuestion = async () => {
        if (gameOver) return
        
        setLoading(true)
        try {
            const response = await fetch(`${BACKEND_URL}/api/survival/question`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    difficulty: difficulty,
                    section: section,
                    excluded_question_ids: excludedQuestionIds
                })
            })

            if (!response.ok) {
                if (response.status === 404) {
                    alert('No more questions available!')
                    navigate('/survival', { replace: true })
                    return
                }
                throw new Error('Failed to fetch question')
            }

            const question = await response.json()
            setCurrentQuestion(question)
            setSelectedAnswer(null)
            setShowFeedback(false)
        } catch (error) {
            console.error('Error fetching question:', error)
            alert('Error loading question. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    const handleAnswerSelect = (questionId, answer) => {
        if (showFeedback) return // Prevent selecting after feedback shown
        
        setSelectedAnswer(answer)
        setShowFeedback(true)
        
        const isCorrect = answer === currentQuestion.correct_answer
        
        // Update stats
        setQuestionsAnswered(prev => prev + 1)
        if (isCorrect) {
            setQuestionsCorrect(prev => prev + 1)
        } else {
            setLives(prev => prev - 1)
        }
        
        // Track answer
        const answerRecord = {
            question_id: questionId,
            user_answer: answer,
            correct_answer: currentQuestion.correct_answer,
            is_correct: isCorrect
        }
        setAnswers(prev => [...prev, answerRecord])
        
        // Add to excluded questions
        setExcludedQuestionIds(prev => [...prev, questionId])
        
        // Check if game over
        if (!isCorrect && lives - 1 <= 0) {
            setGameOver(true)
            // Save session after a short delay
            setTimeout(() => saveSession(), 1500)
        }
    }

    const handleNext = () => {
        if (gameOver) return
        fetchQuestion()
    }

    const saveSession = async () => {
        try {
            // Get user_id from your auth context or wherever you store it
            const userId = user.id
            
            const response = await fetch(`${BACKEND_URL}/api/survival/session/save`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    difficulty: difficulty,
                    section: section,
                    questions_answered: questionsAnswered,
                    questions_correct: questionsCorrect,
                    question_ids: excludedQuestionIds,
                    answers: answers,
                    start_time: startingTime
                })
            })

            if (response.ok) {
                const result = await response.json()
                console.log('Session saved:', result)
            }
        } catch (error) {
            console.error('Error saving session:', error)
        }
    }

    const handlePlayAgain = () => {
        navigate('/survival', { replace: true })
    }

    if (loading && !currentQuestion) {
        return <div className="loading">Loading question...</div>
    }

    if (gameOver) {
        return (
            <GameOver questionsAnswered={questionsAnswered} questionsCorrect={questionsCorrect} handlePlayAgain={handlePlayAgain} />
        )
    }

    return (
        <div className="survival-questions-container">
            {/* Header with lives and stats */}
            <div className="survival-header">
                <div className="lives-container">
                    <span className="lives-label">Lives:</span>
                    {[...Array(3)].map((_, i) => (
                        <span 
                            key={i} 
                            className={`heart ${i < lives ? 'active' : 'lost'}`}
                        >
                            {i < lives ? '❤️' : '🖤'}
                        </span>
                    ))}
                </div>
                <div className="stats-container">
                    <span>Score: {questionsCorrect}/{questionsAnswered}</span>
                    <span className="difficulty-badge">{difficulty}</span>
                    <span className="section-badge">{section}</span>
                </div>
            </div>

            {/* Question */}
            {currentQuestion && (
                <div className="question-container">
                    <SurvivalQuestion
                        question={currentQuestion}
                        index={questionsAnswered + 1}
                        selectedAnswer={selectedAnswer}
                        handleAnswerSelect={handleAnswerSelect}
                        showFeedback={showFeedback}
                        correctAnswer={currentQuestion.correct_answer}
                    />

                    {/* Feedback Section */}
                    {showFeedback && (
                        <div className="feedback-section">
                            {selectedAnswer === currentQuestion.correct_answer ? (
                                <div className="correct-message">
                                    <span className="icon">✅</span>
                                    <h3>Correct!</h3>
                                </div>
                            ) : (
                                <div className="incorrect-message">
                                    <span className="icon">❌</span>
                                    <h3>Wrong!</h3>
                                    <p className="correct-answer-text">
                                        The correct answer was: <strong>{currentQuestion.correct_answer}</strong>
                                    </p>
                                    {currentQuestion.explanation && (
                                        <div className="explanation">
                                            <h4>Explanation:</h4>
                                            <p>{currentQuestion.explanation}</p>
                                        </div>
                                    )}
                                </div>
                            )}

                            {!gameOver && (
                                <button 
                                    onClick={handleNext} 
                                    className="next-button"
                                    disabled={loading}
                                >
                                    {loading ? 'Loading...' : 'Next Question →'}
                                </button>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}