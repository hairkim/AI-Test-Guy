import { React, useState } from 'react';
import { submitTrainingPdf } from '../../services/trainingService';

export default function TrainModel() {
    const [pdf, setPdf] = useState(null)
    const [examName, setExamName] = useState("")
    const [response, setResponse] = useState("")
    const handleSubmit = async (e) => {
        setResponse("");
        e.preventDefault();
        if (!pdf || !examName.trim()) {
          alert("Please select a PDF file and enter an exam name.");
          return;
        }
        
        try {
          const data = await submitTrainingPdf({ pdf, examName });
          setResponse(data.message || "Success!");
        } catch (err) {
          console.error(err);
          setResponse("Upload failed.");
        }
    }

    return (
        <>
            <form onSubmit={handleSubmit}>
                <input
                type="file"
                accept="application/pdf"
                onChange={(e) => setPdf(e.target.files[0])}
                />
                <input
                  type="text"
                  placeholder="Enter exam name (e.g., SAT)"
                  value={examName}
                  onChange={(e) => setExamName(e.target.value)}
                />
                <button type="submit">Upload PDF</button>
            </form>
            <div className="message">{response}</div>
        </>
    )
}
