import React, { useState } from 'react'
import SatQuestion from '../SupportingComponents/SatQuestion.jsx'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../../ClientStuff/AuthContext'
import '../CSS/PracticeQuestions.css'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import StreamingMessage from '../MiscComponents/streaming.jsx'
import 'katex/dist/katex.min.css'
import '../CSS/QuestionsPage.css'

//this is for practice questions (math or english)

export default function PracticeQuestions() {
    const location = useLocation()
    const { session } = useAuth()
    const {questions} = location.state || {}
    const [currentIndex, setCurrentIndex] = useState(0)
    const [userAnswer, setUserAnswer] = useState({})
    const [userQuestion, setUserQuestion] = useState("")
    const [error, setError] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [chatHistory, setChatHistory] = useState([])

    const handleAnswerSelect = (questionId, answer) => {
        setUserAnswer({
            ...userAnswer,
            [questionId]: answer
        })
    }

    const handleNextQuestion = () => {
        setCurrentIndex(currentIndex + 1)
        // Clear chat history for new question
        setChatHistory([])
    }

    const handlePreviousQuestion = () => {
        setCurrentIndex(currentIndex - 1)
        // Clear chat history for new question
        setChatHistory([])
    }

    const handleTypingComplete = (messageIndex) => {
        setChatHistory(prev => {
            const updated = [...prev];
            updated[messageIndex].status = 'complete';
            return updated;
        });
      };

    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;

    const submitPrompt = async () => {
        if (!userQuestion.trim() || !questions[currentIndex]) return;

        setIsLoading(true);
        setError("");

        try {
            const response = await fetch(`${BACKEND_URL}/api/practice-tutor/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session.access_token}`
                },
                body: JSON.stringify({
                    question_id: questions[currentIndex].id,
                    user_question: userQuestion,
                    chat_history: chatHistory
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Add to chat history
            const newChatHistory = [
                ...chatHistory,
                {
                    user: userQuestion,
                    tutor: data.response,
                    timestamp: new Date().toISOString()
                }
            ];
            
            setChatHistory(newChatHistory);
            setUserQuestion(""); // Clear input

        } catch {
            console.error('Error getting tutor response');
            setError('Failed to get tutor response. Please try again.');
        } finally {
            setIsLoading(false);
        }
    }

    // Quick action buttons for common requests
    const requestHint = async () => {
        if (!questions[currentIndex]) return;

        setIsLoading(true);
        try {
            const response = await fetch(`${BACKEND_URL}/api/practice-tutor/step`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session.access_token}`
                },
                body: JSON.stringify({
                    question_id: questions[currentIndex].id,
                    step_requested: "hint"
                })
            });

            const data = await response.json();
            
            setChatHistory([
                ...chatHistory,
                {
                    user: "Can you give me a hint?",
                    tutor: data.content,
                    timestamp: new Date().toISOString()
                }
            ]);

        } catch{
            setError('Failed to get hint. Please try again.');
            console.log('error')
        } finally {
            setIsLoading(false);
        }
    }

    const checkAnswer = async () => {
        const currentQuestion = questions[currentIndex];
        const selectedAnswer = userAnswer[currentQuestion.id];
        
        if (!selectedAnswer) {
            setError('Please select an answer first.');
            return;
        }

        setIsLoading(true);
        try {
            const response = await fetch(`${BACKEND_URL}/api/practice-tutor/step`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session.access_token}`
                },
                body: JSON.stringify({
                    question_id: currentQuestion.id,
                    step_requested: "check_answer",
                    user_attempt: selectedAnswer
                })
            });

            const data = await response.json();
            
            setChatHistory([
                ...chatHistory,
                {
                    user: `I think the answer is ${selectedAnswer}. Is that correct?`,
                    tutor: data.content,
                    timestamp: new Date().toISOString()
                }
            ]);

        } catch {
            setError('Failed to check answer. Please try again.');
        } finally {
            setIsLoading(false);
        }
    }

    const explainConcept = async () => {
        if (!questions[currentIndex]) return;

        setIsLoading(true);
        try {
            const response = await fetch(`${BACKEND_URL}/api/practice-tutor/step`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session.access_token}`
                },
                body: JSON.stringify({
                    question_id: questions[currentIndex].id,
                    step_requested: "explanation"
                })
            });

            const data = await response.json();
            
            setChatHistory([
                ...chatHistory,
                {
                    user: "Can you explain the concept behind this question?",
                    tutor: data.content,
                    timestamp: new Date().toISOString()
                }
            ]);

        } catch {
            setError('Failed to get explanation. Please try again.');
        } finally {
            setIsLoading(false);
        }
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitPrompt();
        }
    }

    return (
        <div>
            {questions && (
                <div className='practice_question_container'>
                    <div className='question_container'>
                        <div className='thesatquestioncontainer'>
                            <SatQuestion 
                                key={questions[currentIndex].id} 
                                question={questions[currentIndex]} 
                                index={currentIndex + 1} 
                                selectedAnswer={userAnswer[questions[currentIndex].id]} 
                                handleAnswerSelect={(questionId, answer) => handleAnswerSelect(questionId, answer)} 
                            />
                        </div>
                        <div className="practice-question-buttons">
                            <button onClick={handlePreviousQuestion} disabled={currentIndex === 0}>
                                Previous
                            </button>
                            <span className="question-counter">
                                Question {currentIndex + 1} of {questions.length}
                            </span>
                            <button onClick={handleNextQuestion} disabled={currentIndex === questions.length - 1}>
                                Next
                            </button>
                        </div>
                        {/* Quick Action Buttons */}
                        <div className="quick-actions">
                            <button 
                                onClick={requestHint} 
                                disabled={isLoading}
                                className="quick-action-btn hint-btn"
                            >
                                💡 Get Hint
                            </button>
                            <button 
                                onClick={checkAnswer} 
                                disabled={isLoading || !userAnswer[questions[currentIndex].id]}
                                className="quick-action-btn check-btn"
                            >
                                ✓ Check Answer
                            </button>
                            <button 
                                onClick={explainConcept} 
                                disabled={isLoading}
                                className="quick-action-btn explain-btn"
                            >
                                📚 Explain Concept
                            </button>
                        </div>
                    </div>
                    
                    <div className='ai_container'>
                        <h2>AI Tutor</h2>
                        {/* Chat History */}
                        <div className='ai_messages_container'>
                            {chatHistory.length === 0 && (
                                <div className="welcome-message">
                                    <p>👋 Hi! I&apos;m your SAT tutor. I can help you with this question by:</p>
                                    <ul>
                                        <li>Giving you hints to guide your thinking</li>
                                        <li>Checking your reasoning</li>
                                        <li>Explaining key concepts</li>
                                        <li>Breaking down the problem step-by-step</li>
                                    </ul>
                                    <p>Just ask me anything or use the quick action buttons above!</p>
                                </div>
                            )}
                            
                            {chatHistory.map((message, index) => (
                                <div className='qpage_messages_container' key={index}>
                                {/* User message with wrapper for right alignment */}
                                <div className='message-wrapper user'>
                                    <div className='chat_box_user_message'>{message.user}</div>
                                </div>
                                
                                {/* AI message with wrapper for left alignment */}
                                <div className='message-wrapper ai'>
                                    <div className='chat_box_ai_message'>
                                    {message.status === 'pending' ? (
                                        <div className="typing-indicator">Loading...</div>
                                    ) : message.status === 'streaming' ? (
                                        <StreamingMessage 
                                            response={message.response} 
                                            onComplete={() => handleTypingComplete(index)}
                                        />
                                    ) : message.status === 'error' ? (
                                        <div>Sorry, I couldn&apos;t process that request.</div>
                                    ) : (
                                        <ReactMarkdown 
                                            remarkPlugins={[remarkMath]}
                                            rehypePlugins={[rehypeKatex]}
                                        >
                                            {message.tutor}
                                        </ReactMarkdown>
                                    )}
                                    </div>
                                </div>
                                </div>
                            ))
                            }
                        </div>
                        <div className='qpage_form'>
                        {error && (
                            <div className="error-message">
                                {error}
                            </div>
                        )}
                        <div className="input-wrapper">
                            <textarea
                                className="prompt auto-resize"
                                value={userQuestion}
                                onChange={(e) => setUserQuestion(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Ask me anything..."
                                disabled={isLoading}
                                rows={1}
                            />
                            <button 
                                className="submit-button"
                                onClick={submitPrompt}
                                disabled={isLoading || !userQuestion.trim()}
                            >
                                {isLoading ? '⏳' : '➤'}
                            </button>
                        </div>
                        </div>  
                    </div>
                </div>
            )}
        </div>
    )
}