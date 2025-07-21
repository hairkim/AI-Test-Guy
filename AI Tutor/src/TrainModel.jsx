import { React, useState } from 'react';

export default function TrainModel() {
    const [pdf, setPdf] = useState(null)
    const [response, setResponse] = useState("")

    const BACKEND_URL = import.meta.env.VITE_BACKEND_PORT

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!pdf) {
          alert("Please select a PDF file.");
          return;
        }
        
        const formData = new FormData();
        formData.append("pdf", pdf);
    
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
                <button type="submit">Upload PDF</button>
            </form>
            <div className="message">{response}</div>
        </>
    )
}