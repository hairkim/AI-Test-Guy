import {React, useState} from 'react'
import './EnglishPage.css'

export default function EnglishPage() {
    const [passage, setPassage] = useState("")
    const [question, setQuestion] = useState("")
    const [isLoading, setIsLoading] = useState(false)

    return (
        <div>
            <form className='form' onSubmit={(e) => { e.preventDefault(); submitPrompt(); }}>
                <div className='text-container'>
                    <textarea
                        className="textbox"
                        value={passage}
                        onChange={(e) => setPassage(e.target.value)}
                        placeholder="Type the necessary passage"
                        disabled={isLoading}
                    />
                    <textarea
                        className="textbox"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="Type the question"
                        disabled={isLoading}
                    />
                </div>
                <button type="submit" disabled={isLoading}>
                    {isLoading ? 'Processing...' : 'Submit'}
                </button>
            </form>
        </div>
    )
}