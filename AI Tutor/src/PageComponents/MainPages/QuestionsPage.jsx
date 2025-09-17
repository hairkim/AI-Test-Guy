import { useState, React, useEffect, useRef } from 'react';
import '../CSS/QuestionsPage.css'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import SubjectToggle from '../SupportingComponents/SubjectToggle.jsx';
import StreamingMessage from '../MiscComponents/streaming';

export default function QuestionsPage() {
    const [question, setQuestion] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [chatHistory, setChatHistory] = useState([]);

    const chatContainerRef = useRef(null);
  
    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [chatHistory]);
  
    const submitPrompt = async () => {
      if (!question.trim()) {
          setError("Please enter a question");
          return;
      }

      // Add conversation with pending status
      const newConversation = {
          question: question.trim(),
          response: null,
          timestamp: new Date(),
          status: 'pending'
      };
      setChatHistory(prev => [...prev, newConversation]);

      const currentQuestion = question;
      setQuestion(""); // Clear input immediately
      setIsLoading(true);
      setError("");

      try {
          const res = await fetch(`${BACKEND_URL}/ask`, {
              method: "POST",
              headers: {
                  "Content-Type": "application/json",
              },
              body: JSON.stringify({ question: currentQuestion }),
          });

          const data = await res.json();

          if (res.ok) {
              // Update the last conversation with the response
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
              // Mark as error
              setChatHistory(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1].status = 'error';
                  return updated;
              });
              setError("Something went wrong.");
          }
      } catch (err) {
          // Mark as error
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

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submitPrompt();
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
          {/* chat history along with chat output */}
          <div className='qpage_chat_box'>
            {chatHistory.length === 0 ? (
              <div className='qpage_no_messages'>
                <div>
                  Type something to start a conversation with Tutor Guy!
                </div>
              </div>
            ) : (
              chatHistory.map((message, index) => (
                <div className='qpage_messages_container' key={index}>
                  {/* User message with wrapper for right alignment */}
                  <div className='message-wrapper user'>
                    <div className='chat_box_user_message'>{message.question}</div>
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
          {error && (
            <div className="error-message">
                {error}
            </div>
          )}
          <div className="input-wrapper">
            <textarea
                className="prompt auto-resize"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything..."
                disabled={isLoading}
                rows={1}
            />
            <button 
                className="submit-button"
                onClick={submitPrompt}
                disabled={isLoading || !question.trim()}
            >
                {isLoading ? '⏳' : '➤'}
            </button>
          </div>
        </div>
      </div>
    )
}
