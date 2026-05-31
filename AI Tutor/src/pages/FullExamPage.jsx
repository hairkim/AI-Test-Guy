import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext.jsx';
import SatQuestion from '../components/questions/SatQuestion.jsx'
import ExamTimer from '../components/timers/ExamTimer.jsx'
import BreakTimer from '../components/timers/BreakTimer.jsx'
import IntermissionTimer from '../components/timers/IntermissionTimer.jsx'
import '../PageComponents/CSS/FullExamPage.css'
import { generateMockExam, getExamSectionModule, submitTestModule } from '../services/satService.js'
import { useQuestionNavigator } from '../hooks/useQuestionNavigator.js'
import { useTimerWarning } from '../hooks/useTimerWarning.js'
import TimerWarning from '../components/exam/TimerWarning.jsx'

export default function FullExamPage() {
    const { examType } = useParams()
    const { user, session } = useAuth();
    const navigate = useNavigate();
    const [questions, setQuestions] = useState([])
    const [testState, setTestState] = useState("idle") // idle, completed, math1, math2, math1_done, english1, english2, english1_done, english2_done, break, error
    const [isLoading, setIsLoading] = useState(false)
    const [userAnswer, setUserAnswer] = useState({})
    const [module, setModule] = useState(1)
    const [examId, setExamId] = useState(null)
    const [score, setScore] = useState(null)
    const [percentage, setPercentage] = useState(null)
    const [mathTimer, setMathTimer] = useState(0);
    const [englishTimer, setEnglishTimer] = useState(0);
    const [breakTimer, setBreakTimer] = useState(0);
    const [currentSectionType, setCurrentSectionType] = useState(null)
    const [sections, setSections] = useState([])
    const [sectionIndex, setSectionIndex] = useState(0)
    const [completedSections, setCompletedSections] = useState([])
    const [intermissionTimer, setIntermissionTimer] = useState(1 * 60)
    const {
        currentIndex,
        resetQuestionIndex,
        selectNextQuestion,
        selectPreviousQuestion,
    } = useQuestionNavigator()
    const { timerWarning, showTimerWarning } = useTimerWarning()


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
                const data = await generateMockExam({
                    examType,
                    token: session.access_token,
                })
                console.log(data.questions)
                setExamId(data.exam_id)
                setQuestions(data.questions)
                setModule(data.module)
                resetQuestionIndex()
                setSectionIndex(0)
                setCurrentSectionType(data.section_type)
                setCompletedSections([])
                setMathTimer(data.math_module_time_limit)
                setEnglishTimer(data.eng_module_time_limit)
                setBreakTimer(data.break_time_limit * 60)
                setSections(data.sections)
                console.log(data.sections)
            } catch (error) {
                console.error("Error generating exam:", error)
                setTestState("error")
                return
            }
            finally {
                setIsLoading(false)
            }
            setTestState("english1")
        }
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
    
        let timeEnded = null

        setQuestions([])
        // Add end time only for module 2
        if (module === 2) {
            timeEnded = new Date().toISOString();
            if(currentSectionType === 'English') {
                //this will take it to intermission timer immediately after finish
                setTestState("break")
            }
        } else if (module === 1) {
            // Set appropriate state for module 2
            if (currentSectionType === 'English') {
                setTestState("english1_done")
            } else if (currentSectionType === 'Math') {
                setTestState("math1_done")
            }
        }
        
        try {
            const data = await submitTestModule({
                sectionType: currentSectionType,
                module,
                examId,
                answers: userAnswer,
                timeEnded,
                token: session.access_token,
            })
            console.log("Submit response:", data)
    
            // Handle module progression
            if (module === 1) {
                // Module 1 completed - load module 2 for same section
                console.log("submit test for module 1 of section")
                setQuestions(data.module2_questions)
                setModule(2)
                resetQuestionIndex()
                setUserAnswer({})
                
            } else if (module === 2) {
                // Module 2 completed - check if there are more sections
                console.log("submit test for module 2 of section")
                setUserAnswer({})
                setScore(data.section_score)
                setPercentage(data.percentage)
                setCompletedSections([...completedSections, currentSectionType])

                const nextSectionIndex = sectionIndex + 1
                
                if (nextSectionIndex < sections.length) {
                    // Move to next section
                    const nextSectionType = sections[nextSectionIndex]
                    
                    if (currentSectionType === 'English' && nextSectionType === 'Math') {
                        // Finished English, take a break before Math
                        console.log("English to Math")
                        setModule(1)
                        setSectionIndex(nextSectionIndex)
                        setCurrentSectionType(nextSectionType)
                        
                        //load the next math section
                        await loadNextSection("Math", nextSectionIndex, 1)
                    } else {
                        // This shouldn't happen in your flow but good to handle
                        await loadNextSection(nextSectionType, nextSectionIndex, 1)
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
            }
    
        } catch (error) {
            console.error("Error submitting test:", error)
            setTestState("error")
        } finally {
            setIsLoading(false)
        }
    }

    const loadNextSection = async (sectionType, sectionIndex, moduleNumber) => {
        try {
            // Call API to get questions for the next section's module 1
            const data = await getExamSectionModule({
                sectionType,
                moduleNumber,
                examId,
                token: session.access_token,
            })

            setQuestions(data.questions)
            setCurrentSectionType(sectionType)
            setSectionIndex(sectionIndex)
            setModule(1)
            resetQuestionIndex()
            setUserAnswer({})
        } catch (error) {
            console.error("Error loading next section:", error)
            setTestState("error")
        }
    }

    const handleBreakEnd = () => {
        setBreakTimer(10 * 60)
        console.log(questions)
        if(questions.length > 0) { 
            setTestState("math1")
        }
    }

    const handleIntermissionEnd = () => {
        setIntermissionTimer(1 * 60) // Reset for next time
        if(currentSectionType === 'Math' && questions.length > 0) {
            setTestState("math2")
        } else if (currentSectionType === 'English' && questions.length > 0) {
            setTestState("english2")
        }
    }

        const handleAnswerSelect = (questionId, answer) => {
        setUserAnswer((prev) => ({
            ...prev,
            [questionId]: answer
        }))
    }

    const handleTimeUp = () => {
        alert("Time is up! submitting current module")
        submitTest()
    }


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
                                onWarning={() => showTimerWarning("Time is running out!")}
                            />
                            <TimerWarning message={timerWarning} />
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
                        <button onClick={selectPreviousQuestion}>Previous</button>
                        <button onClick={() => selectNextQuestion(questions.length)}>Next</button>
                    </div>
                </div>
            )}
            {testState === 'break' && (
                <div className='full_test_break_container'>
                    <BreakTimer 
                        timeLimit={breakTimer}
                        onBreakEnd={handleBreakEnd}
                        isLoading={isLoading}
                    />
                </div>
            )}
            {testState === 'completed' && (
                //TODO: make this into a component 
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
                        timeLimit={intermissionTimer}
                        onIntermissionEnd={handleIntermissionEnd}
                        currentSectionType={currentSectionType}
                        isLoading={isLoading}
                    />
                </div>
            )}
        </div>
    );
}
