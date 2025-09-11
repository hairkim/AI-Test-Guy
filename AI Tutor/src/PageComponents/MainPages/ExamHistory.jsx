import React, { useEffect, useState } from "react";
import { useAuth } from "../../ClientStuff/AuthContext.jsx";
import ExamHistoryRow from "../SupportingComponents/ExamHistoryRow.jsx";
import '../CSS/ExamHistory.css'

export default function ExamHistory() {

    const { session } = useAuth();
    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;

    const [exams, setExams] = useState([]);
    
    useEffect(() => {
        fetchExams();
    }, []);
    
    const fetchExams = async () => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/sat/mock-exam/history`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session.access_token}`
                }
            });
            const data = await response.json();
            setExams(data);
        } catch (error) {
            console.error('Error fetching exams:', error);
        }
    };
    
    return (
        <div>
            <div className='title-container'>
                <h1>Exam History</h1>
            </div>
            {exams.length > 0 ? (
                exams.map((exam) => (
                    <ExamHistoryRow exam={exam} />
                ))
            ) : (
                <p>No exams found</p>
            )}
        </div>
    );
}