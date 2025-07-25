import { React, useState } from 'react';

export default function TrainModel() {
    const [pdf, setPdf] = useState(null)
    const [examName, setExamName] = useState("")
    const [response, setResponse] = useState("")

    const BACKEND_URL = import.meta.env.VITE_BACKEND_PORT

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!pdf || !examName.trim()) {
          alert("Please select a PDF file and enter an exam name.");
          return;
        }
        
        const formData = new FormData();
        formData.append("pdf", pdf);
        formData.append("exam_name", examName);
    
        try {
          const res = await fetch(`${BACKEND_URL}/submit_pdf`, {
            method: "POST",
            body: formData,
          });
    
          const data = await res.json();
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