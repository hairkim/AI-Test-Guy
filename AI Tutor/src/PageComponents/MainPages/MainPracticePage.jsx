//page design layout:
//Once the user goes into the page, it will show practice questions immediately
//Maybe load a select amount of questions and once the user finishes, tell them to come back at a specific amount of time?
//also add the ai tutor on the side
import React, { useEffect, useState } from 'react'
import '../CSS/MainPracticePage.css'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../ClientStuff/AuthContext'
import { getRandomQuestions } from '../../services/satService'

export default function MainPracticePage() {
    const navigate = useNavigate()
    const { session } = useAuth()
    const [questions, setQuestions] = useState([])
    const [isLoading, setIsLoading] = useState(false)
    const [section, setSection] = useState(null)
    const [error, setError] = useState(null)

    const count = 20;
    useEffect(() => {
        if (questions.length === count && !isLoading) {
            // Pass questions and section to the practice page
            navigate('/practice-questions', { 
                state: { 
                    questions: questions
                } 
            })
        }else if(error) {
            alert("There was an error while loading the questions: " + error)
        }
    }, [questions, isLoading, navigate, section])

    useEffect(() => {
        if (section) {
            fetchQuestions()
        }
    }, [section])

    const fetchQuestions = async () => {
        setIsLoading(true)
        setError(null)
        
        try {
            const data = await getRandomQuestions({ section, count, token: session.access_token })
            setQuestions(data)
            setIsLoading(false)
        } catch (error) {
            console.error("Error loading questions:", error)
            setError(error.message)
            setIsLoading(false)
        }
    }

    const handleSectionSelect = (selectedSection) => {
        setSection(selectedSection)
        setQuestions([]) // Clear previous questions
        setError(null)
    }

    return (
        <div className="practice_start_container">
            <div className='math_practice_start'>
                <h1>Math Practice</h1>
                <button onClick={() => handleSectionSelect("Math")} disabled={isLoading}>Start</button>
            </div>
            <div className='english_practice_start'>
                <h1>English Practice</h1>
                <button onClick={() => handleSectionSelect("English")} disabled={isLoading}>Start</button>
            </div>
        </div>
    )
}
