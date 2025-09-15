import { useState, React } from 'react';
import '../CSS/QuestionsPage.css'
import ReactMarkdown from 'react-markdown'

export default function QuestionsPage() {
    const [question, setQuestion] = useState("");
    const [error, setError] = useState("");
    const [answer, setAnswer] = useState("");
    const [isLoading, setIsLoading] = useState(false);
  
    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;
  
    const submitPrompt = async () => {
      if(!question) {
        setError("Please enter a question or image into the field")
        return
      }
  
      setIsLoading(true);
      setError("");
      setAnswer("");
  
      //move onto api stuff
      try {
        const res = await fetch(`${BACKEND_URL}/ask`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ question: question }), // sending { "question": "..." }
        });
    
        const data = await res.json();
    
        if (res.ok) {
          setAnswer(data.solution || "");
          console.log("Response data:", data);
          setError(""); // clear error
        } else {
          setError("Something went wrong.");
        }
      } catch (err) {
        setError("Server error: " + err.message);
      } finally {
        setIsLoading(false);
      }
    }

    return (
      <div className='questions_page_container'>
        <div className='qpage_chat_box'>
          {/* chat history along with chat output */}
          <ReactMarkdown>{answer}</ReactMarkdown>
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
                // onKeyDown={handleKeyDown}
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
