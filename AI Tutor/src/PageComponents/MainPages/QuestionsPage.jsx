import { useState, React, useEffect, useRef } from 'react';
import '../CSS/QuestionsPage.css'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import SubjectToggle from '../SupportingComponents/SubjectToggle.jsx';
import StreamingMessage from '../MiscComponents/streaming';
import DragAndDrop from '../SupportingComponents/DragAndDrop.jsx';

export default function QuestionsPage() {
    const [question, setQuestion] = useState("");
    const [image, setImage] = useState(null);
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [chatHistory, setChatHistory] = useState([]);
    const [userHasScrolled, setUserHasScrolled] = useState(false);

    const chatContainerRef = useRef(null);
    const lastScrollTop = useRef(0);

    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;

    // Handle scroll events - only track if user scrolled UP
    useEffect(() => {
        const container = chatContainerRef.current;
        if (!container) return;

        const handleScroll = () => {
            const currentScrollTop = container.scrollTop;
            
            if (currentScrollTop < lastScrollTop.current) {
                setUserHasScrolled(true);
            }
            
            const { scrollTop, scrollHeight, clientHeight } = container;
            if (scrollTop + clientHeight >= scrollHeight - 5) {
                setUserHasScrolled(false);
            }
            
            lastScrollTop.current = currentScrollTop;
        };

        container.addEventListener('scroll', handleScroll, { passive: true });
        return () => container.removeEventListener('scroll', handleScroll);
    }, []);

    // Simple auto-scroll - only when user hasn't manually scrolled up
    useEffect(() => {
        if (!userHasScrolled && chatContainerRef.current) {
            const container = chatContainerRef.current;
            container.scrollTop = container.scrollHeight;
        }
    }, [chatHistory, userHasScrolled]);

    // Store image function to pass to UnifiedInputComponent
    const storeImage = (base64String) => {
        console.log('storeImage called with:', base64String ? `${base64String.length} chars` : 'null');
        setImage(base64String);
    };

    // Submit function
    const submitPrompt = async () => {
        // Allow submission if either question or image is present
        if (!question.trim() && !image) {
            setError("Please enter a question or upload an image");
            return;
        }

        // Reset scroll state for new conversation
        setUserHasScrolled(false);

        const newConversation = {
            question: question.trim() || "(Image uploaded)",
            hasImage: !!image,
            response: null,
            timestamp: new Date(),
            status: 'pending'
        };
        setChatHistory(prev => [...prev, newConversation]);

        const currentQuestion = question;
        const currentImage = image;
        
        // Clear inputs
        setQuestion("");
        setImage(null);
        
        setIsLoading(true);
        setError("");

        try {
            const requestBody = {
                question: currentQuestion || null,
                image: currentImage || null
            };

            console.log('Sending request with:', {
                hasQuestion: !!requestBody.question,
                hasImage: !!requestBody.image,
                imageLength: requestBody.image?.length
            });

            const res = await fetch(`${BACKEND_URL}/ask`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(requestBody),
            });

            const data = await res.json();

            if (res.ok) {
                setChatHistory(prev => {
                    const updated = [...prev];
                    updated[updated.length - 1] = {
                        ...updated[updated.length - 1],
                        response: data.solution || "",
                        status: 'streaming'
                    };
                    return updated;
                });
                setError("");
            } else {
                setChatHistory(prev => {
                    const updated = [...prev];
                    updated[updated.length - 1].status = 'error';
                    return updated;
                });
                setError(data.detail || "Something went wrong.");
            }
        } catch (err) {
            setChatHistory(prev => {
                const updated = [...prev];
                updated[updated.length - 1].status = 'error';
                return updated;
            });
            setError("Server error: " + err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleTypingComplete = (messageIndex) => {
        setChatHistory(prev => {
            const updated = [...prev];
            updated[messageIndex].status = 'complete';
            return updated;
        });
    };

    return (
        <div className='questions_page_container'>
            <div className='qpage_toggle_buttons'>
                <SubjectToggle />
            </div>
            
            <div className='qpage_chat_box' ref={chatContainerRef}>
                {chatHistory.length === 0 ? (
                    <div className='qpage_no_messages'>
                        <div>Type something or upload an image to start a conversation with Tutor Guy!</div>
                    </div>
                ) : (
                    chatHistory.map((message, index) => (
                        <div className='qpage_messages_container' key={index}>
                            <div className='message-wrapper user'>
                                <div className='chat_box_user_message'>
                                    {message.question}
                                    {message.hasImage && (
                                        <div className='image-indicator'>📷 Image attached</div>
                                    )}
                                </div>
                            </div>
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
                                            {message.response}
                                        </ReactMarkdown>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
            
            <div className='qpage_form'>
                {error && <div className="error-message">{error}</div>}
                
                <DragAndDrop 
                    question={question}
                    setQuestion={setQuestion}
                    onSubmit={submitPrompt}
                    isLoading={isLoading}
                    storeImage={storeImage}
                />
            </div>
        </div>
    );
}