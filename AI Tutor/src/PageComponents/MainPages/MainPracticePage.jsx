//page design layout:
//Once the user goes into the page, it will show practice questions immediately
//Maybe load a select amount of questions and once the user finishes, tell them to come back at a specific amount of time?
//also add the ai tutor on the side
import React, { useEffect, useState } from 'react'
import '../CSS/MainPracticePage.css'
import { useNavigate } from 'react-router-dom'

export default function MainPracticePage() {
    const navigate = useNavigate()
    const [questions, setQuestions] = useState([])
    const [isLoading, setIsLoading] = useState(false)
    const [section, setSection] = useState(null)
    const [error, setError] = useState(null)

    const count = 20;

    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;

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
            // Use GET request with query parameters (matches your backend)
            const response = await fetch(`${BACKEND_URL}/api/sat/questions/random?section=${section}&count=${count}`, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json"
                }
            })

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            const data = await response.json()
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