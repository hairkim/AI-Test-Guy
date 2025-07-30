import { useState, React } from 'react';
import { InlineMath } from 'react-katex';
import './QuestionsPage.css'
import DragAndDrop from './DragAndDrop.jsx'

export default function QuestionsPage() {
    const [question, setQuestion] = useState("");
    const [error, setError] = useState("");
    const [answer, setAnswer] = useState("");
  
    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;
  
    const submitPrompt = async () => {
      if(!question) {
        setError("Please enter a question into the field")
        return
      }
  
      //move onto api stuff
      try {
        const res = await fetch(`${BACKEND_URL}/ask`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ question }), // sending { "question": "..." }
        });
    
        const data = await res.json();
    
        if (res.ok) {
          setAnswer(data.answer);
          console.log(data.answer);
          setError(""); // clear error
        } else {
          setError("Something went wrong.");
        }
      } catch (err) {
        setError("Server error: " + err.message);
      }
    }
  
    return (
      <div className='container'>
        <h2>
          Ask me a question!
        </h2>
        <DragAndDrop />
        <form className='form' onSubmit={(e) => { e.preventDefault(); submitPrompt(); }}>
          <textarea
            className="prompt"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Type your question"
          />
          <button type="submit">Submit</button>
        </form>
        <div className="error" style={{ display: error ? "block" : "none" }}>{error}</div>
        {answer && (
          <div>
            <h3>Answer:</h3>
            <p style={{ fontweight: 'bold' }}>
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
