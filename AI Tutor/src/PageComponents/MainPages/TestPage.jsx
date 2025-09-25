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


//states: idle, active, error, module2_loading, module2_loaded, loading_results, completed

import React, { useState } from 'react'
import '../CSS/MathPage.css'
import SatQuestion from '../SupportingComponents/SatQuestion.jsx'
import { useAuth } from '../../ClientStuff/AuthContext.jsx';
import ExamTimer from '../SupportingComponents/ExamTimer.jsx'
import { useParams } from 'react-router-dom'


export default function TestPage() {
    const { examType } = useParams()
    const { user } = useAuth();
    const [questions, setQuestions] = useState([])
    const [testState, setTestState] = useState("idle")
    const [isLoading, setIsLoading] = useState(false)
    const [currentIndex, setCurrentIndex] = useState(0)
    const [userAnswer, setUserAnswer] = useState({})
    const [module, setModule] = useState(1)
    const [examId, setExamId] = useState(null)
    const [score, setScore] = useState(null)
    const [percentage, setPercentage] = useState(null)
    const [timer, setTimer] = useState(0);
    const [timerWarning, setTimerWarning] = useState('')
    const [currentSectionType, setCurrentSectionType] = useState(null)
    const [completedSections, setCompletedSections] = useState([])
    const [examSections, setExamSections] = useState([])

    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;

    const startTest = async () => {
        setIsLoading(true)
        setUserAnswer({})
        if (!user?.id) {
            console.error("No user data found")
            setTestState("error")
            setIsLoading(false)
            return
        } else {
            console.log("User data found: " + user.id)
        }
    
        try {
            const response = await fetch(`${BACKEND_URL}/api/sat/mock-exam/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    exam_type: examType,
                    user_id: user.id,
                    started_at: new Date().toISOString()
                })
            })
            if (response.ok) {
                const data = await response.json()
                
                // Set timer based on current section
                if (data.section_type === 'Math') {
                    setTimer(data.math_module_time_limit)
                } else if (data.section_type === 'English') {
                    setTimer(data.eng_module_time_limit)
                }
                
                setQuestions(data.questions)
                setExamId(data.exam_id)
                setModule(1)
                setCurrentIndex(0)
                setCurrentSectionType(data.section_type) // Track current section
                
                // For full exam, determine section order
                if (examType === 'full_exam') {
                    setExamSections(['Math', 'English']) // You might get this from the API response
                } else {
                    setExamSections([data.section_type])
                }
                
                console.log("fetching worked, showing some questions: " + data.questions[0].question_text)
                setTestState("active")
            }
        } catch (error) {
            console.error("Error loading questions:", error)
            setTestState("error")
        }
        finally {
            setIsLoading(false)
        }
    }

    const handleTimeUp = () => {
        console.log("time up");
        submitTest()
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

    const handleAnswerSelect = (questionId, answer) => {
        console.log("Question ID:", questionId)
        console.log("Selected Answer:", answer)
        setUserAnswer(prev => ({
            ...prev,
            [questionId]: answer
        }))
    }

    const submitTest = async() => {
        if (!examId || !currentSectionType) {
            console.error("No exam ID or section type found")
            return
        }
        console.log("submitting test")
        if(module === 1) {
            setTestState("module2_loading")
        } else {
            setTestState("loading_results")
        }
        setIsLoading(true)
    
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
            // Use currentSectionType in the URL
            const response = await fetch(`${BACKEND_URL}/api/sat/submit_test/${currentSectionType}/${module}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
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
                setQuestions(data.module2_questions)
                setModule(2)
                setCurrentIndex(0)
                setUserAnswer({})
                setTestState("module2_loaded")
            } else {
                // Module 2 completed - check if there are more sections
                const currentSectionIndex = examSections.indexOf(currentSectionType)
                const hasMoreSections = currentSectionIndex < examSections.length - 1
                
                if (hasMoreSections && examType === 'full_exam') {
                    // Move to next section
                    const nextSectionType = examSections[currentSectionIndex + 1]
                    setCompletedSections([...completedSections, currentSectionType])
                    setCurrentSectionType(nextSectionType)
                    setModule(1) // Reset to module 1 for new section
                    setUserAnswer({})
                    
                    // Load next section's questions (you might need a new API call here)
                    await loadNextSection(nextSectionType)
                } else {
                    // All sections completed - show final results
                    setScore(data.section_score || data.total_exam_score)
                    setPercentage(data.percentage)
                    setTestState("completed")
                }
            }
    
        } catch (error) {
            console.error("Error submitting test:", error)
            setIsLoading(false)
            setTestState("error")
        } finally {
            setIsLoading(false)
        }
    }

    const loadNextSection = async (sectionType) => {
        try {
            // You might need a new API endpoint to get the next section's module 1 questions
            const response = await fetch(`${BACKEND_URL}/api/sat/mock-exam/${examId}/section/${sectionType}/module/1`)
            
            if (response.ok) {
                const data = await response.json()
                setQuestions(data.questions)
                
                // Update timer for new section
                if (sectionType === 'Math') {
                    setTimer(35) // Math module time limit
                } else if (sectionType === 'English') {
                    setTimer(32) // English module time limit
                }
                
                setCurrentIndex(0)
                setTestState("active")
            }
        } catch (error) {
            console.error("Error loading next section:", error)
            setTestState("error")
        }
    }


    return (
        <div className='main_container'>
            {(testState === 'active' || testState === 'module2_active') && (
                <ExamTimer 
                    timeLimit={timer}
                    isActive={testState === 'active' || testState === 'module2_active'}
                    onTimeUp={handleTimeUp}
                    module={module}
                    onWarning={handleTimeWarning}
                />
            )}

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
            {testState === 'idle' && (
                <div className="start_page">
                    <h1>{examType === 'math_only' ? 'Math Test Page' : 'English Test Page'}</h1>
                    <div className='start_button'>
                        <button onClick={startTest} disabled={isLoading}>
                            {!isLoading ? 'Start Test' : 'Loading...'}
                        </button>
                        <div className='test-info'>
                            {examType === 'math_only' ? (
                                <>
                                    <h2>You are about to take a practice math only exam</h2>
                                    <p>The test includes 2 modules, each with 22 questions</p>
                                    <p>You will be given module 2 questions based on previous scoring</p>
                                    <p>There is no penalty for wrong answers</p>
                                    <p>Good luck!</p>
                                </>
                            ) : (
                                <>
                                    <h2>You are about to take a practice english only exam</h2>
                                    <p>The test includes 2 modules, each with 27 questions</p>
                                    <p>You will be given module 2 questions based on previous scoring</p>
                                    <p>There is no penalty for wrong answers</p>
                                    <p>Good luck!</p>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}
            {(testState === 'active' || testState === 'module2_active') && (
                <div className="test_page">
                    <div className="section-info">
                        <h2>Section: {currentSectionType} - Module {module}</h2>
                        {examType === 'full_exam' && (
                            <p>Progress: {completedSections.length + 1} of {examSections.length} sections</p>
                        )}
                    </div>
                    <SatQuestion 
                        key={questions[currentIndex].id} 
                        question={questions[currentIndex]} 
                        index={currentIndex + 1} 
                        selectedAnswer={userAnswer[questions[currentIndex].id]} 
                        handleAnswerSelect={(questionId, answer) => handleAnswerSelect(questionId, answer)} 
                    />
                    <div className="button_container">
                        <button onClick={() => selectPreviousQuestion()}>Previous</button>
                        <button onClick={() => selectNextQuestion()}>Next</button>
                    </div>
                    <div className='submit_container'>
                        <button onClick={submitTest}>Submit {currentSectionType} Module {module}</button>
                    </div>   
                </div>
            )}
            {testState === 'loading_results' && (
                <div className="loading_results">
                    <h1>Loading Results...</h1>
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
            {(testState === 'module2_loaded' || testState === 'module2_loading') && (
                <div className="math_loading_page">
                    <div className='test-info-header'>
                        <h1>You have reached the end of Module 1</h1>
                    </div>
                    <p>Module 2 will begin loading in a moment</p>
                    <p>Module will be based on your previous scoring</p>
                    <p>Good luck!</p>
                    <button onClick={() => setTestState('module2_active')} disabled={isLoading}>{isLoading ? 'Loading Module 2' : 'Start Module 2'}</button>
                </div>
            )}
        </div>
    )
}
