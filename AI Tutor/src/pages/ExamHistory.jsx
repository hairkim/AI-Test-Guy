import React, { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext.jsx";
import ExamHistoryRow from "../components/history/ExamHistoryRow.jsx";
import { getMockExamHistory } from "../services/satService.js";
import '../PageComponents/CSS/ExamHistory.css'

export default function ExamHistory() {

    const { session } = useAuth();

    const [exams, setExams] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    
    useEffect(() => {
        fetchExams();
    }, []);
    
    const fetchExams = async () => {
        setIsLoading(true);
        try {
            const data = await getMockExamHistory({ token: session.access_token });
            setExams(data);
        } catch (error) {
            console.error('Error fetching exams:', error);
        } finally {
            setIsLoading(false);
        }
    };
    
    return (
        <div>
            <div className='title-container'>
                <h1>Exam History</h1>
            </div>
            {isLoading && (
                <div className='history-loading-container'>
                    <p>Loading exams...</p>
                </div>
            )}
            {(!isLoading && exams.length > 0) && (
                exams.map((exam) => (
                    <ExamHistoryRow key={exam.id} exam={exam} />
                ))
            )}
            {(!isLoading && exams.length === 0) && (
                <div className='history-no-exams-container'>
                    <p>No exams found</p>
                </div>
            )}
        </div>
    );
}
