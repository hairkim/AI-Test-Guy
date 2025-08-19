import {React, useState} from 'react'
import './EnglishPage.css'

export default function EnglishPage() {
    const [passage, setPassage] = useState("")
    const [question, setQuestion] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [answer, setAnswer] = useState("") // to store backend response
    const [explanation, setExplanation] = useState("")
    const [error, setError] = useState("")

    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;

    const submitPrompt = async () => {
        setError("")
        setAnswer("")
        setExplanation("")

        if (!question.trim()) {
            setError("Question cannot be empty.")
            return
        }

        setIsLoading(true)
        try {
            console.log("the question: " + question)
            console.log("the passage: " + passage)
            const response = await fetch(`${BACKEND_URL}/ask_english`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question,
                    passage: passage || null // send null if empty
                })
            })

            if (!response.ok) {
                throw new Error(`Backend error: ${response.statusText}`)
            }

            const data = await response.json()
            console.log("the data: " + JSON.stringify(data))
            if(data) {
                setAnswer(data.answer || "No answer returned.")
                setExplanation(data.why || "No explanation returned.")
            } else {
                setError("No data returned from backend.")
            }
        } catch (err) {
            console.error(err)
            setError(err.message || "An unexpected error occurred.")
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div>
            <form 
                className='form' 
                onSubmit={(e) => { e.preventDefault(); submitPrompt(); }}
            >
                <div className='text-container'>
                    <textarea
                        className="textbox"
                        value={passage}
                        onChange={(e) => setPassage(e.target.value)}
                        placeholder="Type the necessary passage (optional)"
                        disabled={isLoading}
                    />
                    <textarea
                        className="textbox"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="Type the question"
                        disabled={isLoading}
                        required
                    />
                </div>
                <button type="submit" disabled={isLoading}>
                    {isLoading ? 'Processing...' : 'Submit'}
                </button>
            </form>

            {error && <p className="error">{error}</p>}
            {answer && (
                <div className="answer-box">
                    <h3>Answer:</h3>
                    <p>{answer}</p>
                </div>
            )}
            {explanation && (
                <div className="explanation-box">
                    <h3>Explanation:</h3>
                    <p>{explanation}</p>
                </div>
            )}
        </div>
    )
}