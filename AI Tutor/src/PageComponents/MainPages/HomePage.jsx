import React, { useState, useEffect } from 'react';
import ProfilePicture from '../SupportingComponents/ProfilePicture.jsx'
import TaskComponent from '../SupportingComponents/TaskComponent.jsx'
import '../CSS/HomePage.css'
import { useAuth } from '../../ClientStuff/AuthContext.jsx'
import ScoreCircle from '../SupportingComponents/ExamCircle.jsx'
import { useProtectedNavigation } from '../../ClientStuff/UserProtectedNav.js'

export default function HomePage() {
    const { navigateWithAuth } = useProtectedNavigation()
    const { user, session } = useAuth();
    const pages = ['Practice Exam', 'Practice Questions', 'Ask TutorGuy', 'Exam History']
    const tasks = ['Daily 5 Math Questions','Daily 5 English Questions','Take a Practice Exam']
    const pageRoute = (page) => {
        switch (page) {
            case 'Practice Exam':
                navigateWithAuth('/take_a_test')
                break;
            case 'Practice Questions':
                navigateWithAuth('/practice') // make new route later
                break;
            case 'Ask TutorGuy':
                navigateWithAuth('/query')
                break;
            case 'Exam History':
                navigateWithAuth('/exam_history')
                break;
        }
    }

    const [recentExams, setRecentExams] = useState([])
    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;

    useEffect(() => {
        const loadRecentExams = async () => {
            const exams = await fetchMostRecentExams()
            setRecentExams(exams)
        }
        
        if (session) { // Only fetch when authenticated
            loadRecentExams()
        }
        else {
            // Clear exam data when logged out
            setRecentExams([])
        }
    }, [session])

    //fetch the 2 or 3 most recent exams
    const fetchMostRecentExams = async () => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/sat/mock-exam/history`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session.access_token}` // Include auth token
                }
            })
    
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }
    
            const allExams = await response.json()
            
            // Sort by created_at descending (most recent first) and take first 2
            const recentExams = allExams
                .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                .slice(0, 2)
            
            return recentExams
        } catch (error) {
            console.error('Error fetching recent exams:', error)
            return [] // Return empty array if error
        }
    }

    return (
        <div className="home-page">
            {/* Div for entire header (will be flexbox) */}
            <div className='header-component'>
                <div className='left-side'>
                    <div className='top'>
                        <h1>Welcome {user?.user_metadata?.display_name}</h1>
                    </div>
                    <div className='bottom'>
                        {pages.map((page, index) => (
                            <button key={index} onClick={() => pageRoute(page)}>{page}</button>
                        ))}
                    </div>
                </div>
                <div className='right-side'>
                    <ProfilePicture />
                </div>
            </div>

            {/* Middle Content (Daily Tasks / Level) */}
            <div className='middle-content'>
                <div className='most-recent-exam'>
                    <h2>Most Recent Exam Score</h2>
                    {recentExams.length > 0 && (
                        <ScoreCircle examType={recentExams[0].exam_type} score={recentExams[0].score} />
                    )}
                </div>
                <div className='daily-tasks'>
                    <h2>Daily Tasks</h2>
                    <ul className='tasks'>
                        {tasks.map((task, index) => (
                            // text, completed, onToggleComplete
                            <TaskComponent key={index} text={task} completed={false} onToggleComplete={() => {}} />
                        ))}
                    </ul>
                </div>
                <div className='level'>
                    <h2>Level Portion I need to work on</h2>
                </div>
            </div>

            {/* Bottom content is for previous exam scores */}
            <div className='bottom-content'>
                <h2>Previous Exam Scores</h2>
            </div>
        </div>
    )
}