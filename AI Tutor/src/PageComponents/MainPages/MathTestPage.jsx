import React, { useState } from 'react'
import '../CSS/MathTestPage.css'
import { useAuth } from '../../ClientStuff/AuthContext.jsx';
import { useParams } from 'react-router-dom'
import SatQuestion from '../SupportingComponents/SatQuestion.jsx'
import ExamTimer from '../SupportingComponents/ExamTimer.jsx'
import IntermissionTimer from '../SupportingComponents/IntermissionTimer.jsx'

export default function MathTestPage() {
    const { examType } = useParams()
    const { user, session } = useAuth();
    const [questions, setQuestions] = useState([])
    const [testState, setTestState] = useState("idle")
    const [isLoading, setIsLoading] = useState(false)
    const [currentIndex, setCurrentIndex] = useState(0)
    const [userAnswer, setUserAnswer] = useState({})
    const [module, setModule] = useState(1)
    const [examId, setExamId] = useState(null)
    const [score, setScore] = useState(null)
    const [percentage, setPercentage] = useState(null)
    const [timer, setTimer] = useState(0)
    const [timerWarning, setTimerWarning] = useState('')

    //intermission time limit
    const intermissionTimeLimit = 60

    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;

    const startTest = async () => {
        setIsLoading(true)
        setUserAnswer({})
        if(!user?.id) {
            alert("Please sign in to take a test")
            setIsLoading(false)
            return
        }
        try {
            const response = await fetch(`${BACKEND_URL}/api/sat/mock-exam/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session.access_token}`,
                },
                body: JSON.stringify({
                    exam_type: examType,
                    user_id: user.id,
                    started_at: new Date().toISOString()
                })
            })
            if (response.ok) {
                const data = await response.json()
                
                setTimer(data.math_module_time_limit)
                // setTimer(6)
                console.log(data.questions)
                setQuestions(data.questions)
                setExamId(data.exam_id)
                setModule(1)
                setCurrentIndex(0)
                
                console.log("fetching worked, showing some questions: " + data.questions[0].question_text)
            }
        } catch (error) {
            console.error("Error loading questions:", error)
            setTestState("error")
        }
        finally {
            setTestState("math1")
            setIsLoading(false)
        }
    }

    const handleAnswerSelect = (questionId, answer) => {
        setUserAnswer((prev) => ({
            ...prev,
            [questionId]: answer
        }))
        console.log(Object.keys(userAnswer).length)
    }

    const handleTimeUp = () => {
        console.log("Time is up, submitting test")
        //submitTest()
    }

    const handleTimeWarning = (message) => {
        setTimerWarning(message)
        // Clear warning after 5 seconds
        setTimeout(() => setTimerWarning(''), 5000)
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

    const onIntermissionEnd = () => {
        setTestState('math2')
    }

    const submitTest = async() => {
        if (!examId) {
            console.error("No exam ID found")
            return
        }
        setIsLoading(true)
        console.log("submitting test")
        if(module === 1) {
            setTestState("break")
        } else {
            setTestState("completed")
        }

        const requestBody = {
            exam_id: examId,
            answers: userAnswer,
            module: module
        };
        
        // Add end time only for module 2
        if (module === 2) {
            requestBody.time_ended = new Date().toISOString();
        }
        
        try {
            const response = await fetch(`${BACKEND_URL}/api/sat/submit_test/${'Math'}/${module}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session.access_token}`,
                },
                body: JSON.stringify(requestBody)
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

            } else {
                // Module 2 completed - show final results
                setScore(data.section_score)
                setPercentage(data.percentage)
            }

        } catch (error) {
            console.error("Error submitting test:", error)
            setIsLoading(false)
            setTestState("error")
        } finally {
            setIsLoading(false)
        }
    }
    
    return (
        <div className='math_main_container'>
            {/* idle test state (beginning) */}
            {testState === 'idle' && (
                <div className='math_idle_container'>
                    <div className='math_idle_text'>
                        <h2>You are about to take a practice math only exam</h2>
                        <p>The test includes 2 modules, each with 22 questions</p>
                        <p>You will be given module 2 questions based on previous scoring</p>
                        <p>There is no penalty for wrong answers</p>
                        <p>Good luck!</p>
                    </div>
                    <div className='math_idle_button'>
                        <button onClick={startTest} disabled={isLoading}>Start Test</button>
                    </div>
                </div>
            )}
            {/* math/english test states */}
            {((testState === 'math1' || testState === 'math2' || testState === 'english1' || testState === 'english2') && questions.length > 0) && (
                <div className='full_test_container'>
                    <div className="full_section_info">
                        <h2>Section: Math - Module {module}</h2>
                        <div className='full_timer_container'>
                            <ExamTimer 
                                timeLimit={timer}
                                isActive={testState === 'math1' || testState === 'math2' || testState === 'english1' || testState === 'english2'}
                                onTimeUp={handleTimeUp}
                                module={module}
                                onWarning={() => handleTimeWarning("Time is running out!")}
                            />
                            {/* Warning message */}
                            {timerWarning && (
                                <div style={{
                                    position: 'fixed',
                                    top: '100px',
                                    right: '20px',
                                    backgroundColor: '#FEF3C7',
                                    border: '1px solid #F59E0B',
                                    borderRadius: '6px',
                                    padding: '8px 12px',
                                    fontSize: '14px',
                                    color: '#92400E',
                                    zIndex: 1001
                                }}>
                                    {timerWarning}
                                </div>
                            )}
                            <button className='full_submit_button' onClick={submitTest} disabled={questions.length !== Object.keys(userAnswer).length}>Submit Module</button>
                        </div>
                    </div>
                    <SatQuestion
                        question={questions[currentIndex]}
                        index={currentIndex + 1}
                        selectedAnswer={userAnswer[questions[currentIndex].id]}
                        handleAnswerSelect={(questionId, answer) => handleAnswerSelect(questionId, answer)}
                    />
                    <div className='full_test_buttons'>
                        <button onClick={() => selectPreviousQuestion()}>Previous</button>
                        <button onClick={() => selectNextQuestion()}>Next</button>
                    </div>
                </div>
            )}
            {testState === 'break' && (
                <IntermissionTimer
                    timeLimit={intermissionTimeLimit}
                    onIntermissionEnd={onIntermissionEnd}
                    currentSectionType="Math"
                    isLoading={isLoading}
                />
            )}
            {testState === 'completed' && (
                <div className='math_results_container'>
                    <h2>Results</h2>
                    <p>Score: {score}</p>
                    <p>Percentage: {percentage}</p>
                    <button onClick={() => setTestState('idle')}>Retake Test</button>
                </div>
            )}
        </div>
    )
}