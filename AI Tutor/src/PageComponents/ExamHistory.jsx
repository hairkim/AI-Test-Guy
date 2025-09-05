import React, { useEffect, useState } from "react";
import { useAuth } from "../ClientStuff/AuthContext.jsx";

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
            {exams.length > 0 ? (
                exams.map((exam) => (
                    <div key={exam.id}>
                        <h2>Exam {exam.id}</h2>
                        <p>Exam Type: {exam.exam_type}</p>
                        <p>Module: {exam.module}</p>
                        <p>Total Questions: {exam.total_questions}</p>
                        <p>Score: {exam.score}</p>
                        <p>Percentage: {exam.percentage}</p>
                    </div>
                ))
            ) : (
                <p>No exams found</p>
            )}
        </div>
    );
}