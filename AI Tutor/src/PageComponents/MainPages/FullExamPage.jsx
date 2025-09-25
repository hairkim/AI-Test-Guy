import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../../ClientStuff/AuthContext.jsx';
import SatQuestion from '../SupportingComponents/SatQuestion.jsx'
import ExamTimer from '../SupportingComponents/ExamTimer.jsx'
import BreakTimer from '../SupportingComponents/BreakTimer.jsx'
import IntermissionTimer from '../SupportingComponents/IntermissionTimer.jsx'
import '../CSS/FullExamPage.css'

export default function FullExamPage() {
    const { examType } = useParams()
    const { user, session } = useAuth();
    const navigate = useNavigate();
    const [questions, setQuestions] = useState([])
    const [testState, setTestState] = useState("idle") // idle, completed, math1, math2, math1_done, english1, english2, english1_done, english2_done, break, error
    const [isLoading, setIsLoading] = useState(false)
    const [currentIndex, setCurrentIndex] = useState(0)
    const [userAnswer, setUserAnswer] = useState({})
    const [module, setModule] = useState(1)
    const [examId, setExamId] = useState(null)
    const [score, setScore] = useState(null)
    const [percentage, setPercentage] = useState(null)
    const [mathTimer, setMathTimer] = useState(0);
    const [englishTimer, setEnglishTimer] = useState(0);
    const [breakTimer, setBreakTimer] = useState(0);
    const [timerWarning, setTimerWarning] = useState('')
    const [currentSectionType, setCurrentSectionType] = useState(null)
    const [sections, setSections] = useState([])
    const [sectionIndex, setSectionIndex] = useState(0)
    const [completedSections, setCompletedSections] = useState([])
    const [intermissionTimer, setIntermissionTimer] = useState(1 * 60)

    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;


    //start with english modules first then go onto math modules
    const startTest = async () => {
        setIsLoading(true)
        setUserAnswer({})
        setSections([])
        if (!user?.id) {
            console.error("No user data found")
            setTestState("error")
            setIsLoading(false)
            return
        } else {
            try {
                const response = await fetch(`${BACKEND_URL}/api/sat/mock-exam/generate`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${session.access_token}`,
                    },
                    body: JSON.stringify({
                        exam_type: examType,
                        user_id: user.id,
                        started_at: new Date().toISOString()
                    })
                })
                if (response.ok) {
                    const data = await response.json()
                    console.log(data.questions)
                    setExamId(data.exam_id)
                    setQuestions(data.questions)
                    setModule(data.module)
                    setCurrentIndex(0)
                    setSectionIndex(0)
                    setCurrentSectionType(data.section_type)
                    setCompletedSections([])
                    setMathTimer(data.math_module_time_limit)
                    setEnglishTimer(data.eng_module_time_limit)
                    setBreakTimer(data.break_time_limit * 60)
                    setSections(data.sections)
                } else {
                    console.error("Failed to generate exam")
                    setTestState("error")
                    setIsLoading(false)
                }
            } catch (error) {
                console.error("Error generating exam:", error)
                setTestState("error")
                setIsLoading(false)
            }
            finally {
                setTestState("english1")
                setIsLoading(false)
            }
        }
    }

    const handleAnswerSelect = (questionId, answer) => {
        setUserAnswer((prev) => ({
            ...prev,
            [questionId]: answer
        }))
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

    const handleTimeUp = () => {
        alert("Time is up! submitting current module")
        submitTest()
    }


    //logic for submitting in full exam:
    //if english module 1, load english module 2 questions and finish english portion
    //if english module2 complete, give user break time
    //if english module 2 complete, load math module 1 questions
    //if math module 1 complete, load math module 2 questions
    //if math module 2 complete, submit exam
    const submitTest = async() => {
        if (!examId) {
            console.error("No exam ID found")
            return
        }
        setIsLoading(true)
    
        console.log("submitting test for:", currentSectionType, "module:", module)
    
        const requestBody = {
            exam_id: examId,
            answers: userAnswer,
            module: module
        };
        
        // Add end time only for module 2
        if (module === 2) {
            requestBody.time_ended = new Date().toISOString();
        } else if (module === 1) {
            // Set appropriate state for module 2
            if (currentSectionType === 'English') {
                setTestState("english1_done")
            } else if (currentSectionType === 'Math') {
                setTestState("math1_done")
            }
        }
        
        try {
            const response = await fetch(`${BACKEND_URL}/api/sat/submit_test/${currentSectionType}/${module}`, {
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
    
            // Handle module progression
            if (module === 1) {
                // Module 1 completed - load module 2 for same section
                setQuestions(data.module2_questions)
                setModule(2)
                setCurrentIndex(0)
                setUserAnswer({})
                
            } else if (module === 2) {
                // Module 2 completed - check if there are more sections
                setUserAnswer({})
                setScore(data.section_score)
                setPercentage(data.percentage)
                setCompletedSections([...completedSections, currentSectionType])
                
                // Check if this is a full exam and there are more sections
                if (examType === 'full_exam') {
                    const nextSectionIndex = sectionIndex + 1
                    
                    if (nextSectionIndex < sections.length) {
                        // Move to next section
                        const nextSectionType = sections[nextSectionIndex]
                        
                        if (currentSectionType === 'English' && nextSectionType === 'Math') {
                            // Finished English, take a break before Math
                            setTestState("break")
                            setModule(1)
                            setSectionIndex(nextSectionIndex)
                            setCurrentSectionType(nextSectionType)
                        } else {
                            // This shouldn't happen in your flow but good to handle
                            await loadNextSection(nextSectionType, nextSectionIndex)
                        }
                    } else {
                        // All sections completed
                        setTestState("completed")
                        // data should contain total_exam_score for full exam
                        if (data.total_exam_score) {
                            console.log("sending total score: ", data.total_exam_score)
                            setScore(data.total_exam_score)
                        }
                    }
                } else {
                    // Single section exam completed
                    setTestState("completed")
                }
            }
    
        } catch (error) {
            console.error("Error submitting test:", error)
            setTestState("error")
        } finally {
            setIsLoading(false)
        }
    }

    const loadNextSection = async (sectionType, sectionIndex) => {
        try {
            setIsLoading(true)
            
            // Call API to get questions for the next section's module 1
            const response = await fetch(`${BACKEND_URL}/api/sat/mock-exam/section/${sectionType}/module/${module}`, {
                headers: {
                    'Authorization': `Bearer ${session.access_token}`,
                    'X-Exam-ID': examId,
                    'Content-Type': 'application/json'
                }
            })
            
            if (response.ok) {
                const data = await response.json()
                setQuestions(data.questions)
                setCurrentSectionType(sectionType)
                setSectionIndex(sectionIndex)
                setModule(1)
                setCurrentIndex(0)
                setUserAnswer({})
                
                // Set appropriate test state
                if (sectionType === 'Math') {
                    setTestState("math1")
                } else if (sectionType === 'English') {
                    setTestState("english1")
                }
            } else {
                throw new Error("Failed to load next section")
            }
        } catch (error) {
            console.error("Error loading next section:", error)
            setTestState("error")
        } finally {
            setIsLoading(false)
        }
    }

    const startMathSection = () => {
        loadNextSection('Math', sectionIndex)
    }

    const handleBreakEnd = () => {
        setBreakTimer(10 * 60) // Reset for next time
        startMathSection()
    }

    const handleIntermissionEnd = () => {
        setIntermissionTimer(1 * 60) // Reset for next time
        if(currentSectionType === 'Math') {
            setTestState("math2")
        } else if (currentSectionType === 'English') {
            setTestState("english2")
        }
    }

    useEffect(() => {
        if (testState === 'break' && breakTimer > 0) {
            const timer = setInterval(() => {
                setBreakTimer(prev => {
                    if (prev <= 1) {
                        handleBreakEnd()
                        return 0
                    }
                    return prev - 1
                })
            }, 1000)
    
            return () => clearInterval(timer)
        }
    }, [testState, breakTimer])

    useEffect(() => {
        if ((testState === 'english1_done' || testState === 'math1_done') && intermissionTimer > 0) {
            const timer = setInterval(() => {
                setIntermissionTimer(prev => {
                    if (prev <= 1) {
                        handleIntermissionEnd()
                        return 0
                    }
                    return prev - 1
                })
            }, 1000)
    
            return () => clearInterval(timer)
        }
    }, [testState, intermissionTimer])


    return (
        <div className='full_exam_main_container'>
            {testState === 'idle' && (
             <div className="full_idle_container">
                    <div className='full_idle_text'>
                        <h2>You are about to take a full SAT Practice Exam</h2>
                        <p>The test includes 2 modules, each with 22 questions</p>
                        <p>The English section will have 27 questions each module</p>
                        <p>The Math section will have 22 questions each module</p>
                        <p>You will be given module 2 questions based on previous scoring</p>
                        <p>There is no penalty for wrong answers</p>
                        <p>Good luck!</p>
                    </div>
                    <div className='full_idle_button'>
                        <button onClick={startTest} disabled={isLoading}>Start Test</button>
                    </div>
                </div>
            )}
            {((testState === 'math1' || testState === 'math2' || testState === 'english1' || testState === 'english2') && questions.length > 0) && (
                <div className='full_test_container'>
                    <div className="full_section_info">
                        <h2>Section: {currentSectionType} - Module {module}</h2>
                        <div className='full_timer_container'>
                            <ExamTimer 
                                timeLimit={(testState === 'math1' || testState === 'math2') ? mathTimer : englishTimer}
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
                <div className='full_test_break_container'>
                    <BreakTimer 
                        timeRemaining={breakTimer}
                        onBreakEnd={handleBreakEnd}
                    />
                </div>
            )}
            {testState === 'completed' && (
                <div className='full_test_completed_container'>
                    <h2>Test Completed</h2>
                    <p>Thank you for taking the test</p>
                    <p>Score: {score}</p>
                    <p>Percentage: {percentage}</p>
                    <button onClick={() => navigate('/')}>Back to Dashboard</button>
                </div>
            )}
            {(testState === 'english1_done' || testState === 'math1_done') && (
                <div className='full_test_intermission_container'>
                    <IntermissionTimer
                        timeRemaining={intermissionTimer}
                        onIntermissionEnd={handleIntermissionEnd}
                        currentSectionType={currentSectionType}
                    />
                </div>
            )}
        </div>
    );
}