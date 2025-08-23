import { useState, React } from 'react';
import { InlineMath } from 'react-katex';
import './QuestionsPage.css'
import DragAndDrop from './DragAndDrop.jsx'
import StepByStepExplanation from './StepByStepExplanation.jsx'

export default function QuestionsPage() {
    const [question, setQuestion] = useState("");
    const [error, setError] = useState("");
    const [answer, setAnswer] = useState("");
    const [solution, setSolution] = useState("");
    const [explanationSteps, setExplanationSteps] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [image, setImage] = useState("");
  
    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;
  
    const submitPrompt = async () => {
      if(!question && !image) {
        setError("Please enter a question or image into the field")
        return
      }
      // console.log(image);
  
      setIsLoading(true);
      setError("");
      setSolution("");
      setExplanationSteps([]);
      setAnswer("");
  
      //move onto api stuff
      try {
        const res = await fetch(`${BACKEND_URL}/ask`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ question: question, image: image}), // sending { "question": "..." }
        });
    
        const data = await res.json();
    
        if (res.ok) {
          // Handle new structured response format
          if (data.solution && data.explanation_steps) {
            setSolution(data.solution);
            setExplanationSteps(data.explanation_steps);
          }
          // Keep backward compatibility
          setAnswer(data.answer || "");
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
      <div className='container'>
        <h2>
          Ask me a question!
        </h2>
        <DragAndDrop storeImage={setImage} />
        <form className='form' onSubmit={(e) => { e.preventDefault(); submitPrompt(); }}>
          <textarea
            className="prompt"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Type your question"
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Processing...' : 'Submit'}
          </button>
        </form>
        
        <div className="error" style={{ display: error ? "block" : "none" }}>{error}</div>
        
        {isLoading && (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Analyzing your question and generating explanation...</p>
          </div>
        )}
        
        {/* New structured explanation display */}
        {(solution || explanationSteps.length > 0) && (
          <StepByStepExplanation 
            solution={solution} 
            explanationSteps={explanationSteps} 
          />
        )}
        
        {/* Fallback for old format - keep for backward compatibility */}
        {answer && !solution && explanationSteps.length === 0 && (
          <div className="legacy-answer">
            <h3>Answer:</h3>
            <p style={{ fontWeight: 'bold' }}>
              {answer.split(/(\$[^$]*\$)/g).map((part, i) =>
                part.startsWith('$') && part.endsWith('$') ? (
                  <InlineMath key={i} math={part.slice(1, -1)} />
                ) : (
                  <span key={i}>{part}</span>
                )
              )}
            </p>
          </div>
        )}
      </div>
    )
}
