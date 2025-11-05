import React, { useState, useEffect } from 'react';
import ProfilePicture from '../SupportingComponents/ProfilePicture.jsx'
import TaskComponent from '../SupportingComponents/TaskComponent.jsx'
import '../CSS/HomePage.css'
import { useAuth } from '../../ClientStuff/AuthContext.jsx'
import ScoreCircle from '../SupportingComponents/ExamCircle.jsx'
import SchoolScroller from '../SupportingComponents/SchoolScroller.jsx'
import { useProtectedNavigation } from '../../ClientStuff/UserProtectedNav.js'

export default function HomePage() {
    const { navigateWithAuth } = useProtectedNavigation()
    const { user, session } = useAuth();
    const pages = ['Practice Exam', 'Practice Questions', 'Survival', 'Ask TutorGuy', 'Exam History']
    const pageRoute = (page) => {
        switch (page) {
            case 'Practice Exam':
                navigateWithAuth('/take_a_test')
                break;
            case 'Practice Questions':
                navigateWithAuth('/practice')
                break;
            case 'Survival':
                navigateWithAuth('/survival')
                break;
            case 'Ask TutorGuy':
                navigateWithAuth('/query')
                break;
            case 'Exam History':
                navigateWithAuth('/exam_history')
                break;
        }
    }

    const [recentExams, setRecentExams] = useState(null)
    const [userTasks, setUserTasks] = useState([])
    const BACKEND_URL = `${import.meta.env.VITE_BACKEND_PORT}`;

    useEffect(() => {
        const loadRecentExams = async () => {
            const exams = await fetchMostRecentExams()
            console.log("exams: ", exams)
            setRecentExams(exams)
            console.log("recent exams: ", recentExams)
        }

        const loadUserTasks = async () => {
            const tasks = await fetchUserTasks()
            console.log("tasks: ", tasks)
            setUserTasks(tasks)
        }
        
        if (session) { // Only fetch when authenticated
            loadRecentExams()
            loadUserTasks()
        }
        else {
            // Clear exam data when logged out
            setRecentExams(null)
            setUserTasks([])
        }
    }, [session?.access_token])


    const fetchMostRecentExams = async () => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/sat/mock-exam/history`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session.access_token}`
                }
            })
    
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }
    
            const allExams = await response.json()
            
            // Filter for completed exams only, then get the most recent one
            const completedExams = allExams.filter(exam => exam.completed_at !== null)
            
            if (completedExams.length === 0) {
                console.log("No completed exams found")
                return null // or [] if you prefer empty array
            }
            
            // Sort by completed_at descending and take the first (most recent)
            const mostRecentCompleted = completedExams
                .sort((a, b) => new Date(b.completed_at) - new Date(a.completed_at))[0]
            console.log(mostRecentCompleted)
            return mostRecentCompleted
        } catch (error) {
            console.error('Error fetching recent exams:', error)
            return null // Return null if error
        }
    }

    const fetchUserTasks = async () => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/daily/tasks/generate-daily`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session.access_token}`
                }
            })

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            const tasks = await response.json()
            console.log(tasks)
            return tasks.tasks
        } catch (error) {
            console.error('Error fetching tasks:', error)
            return null // Return null if error
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
                    {recentExams ? (
                        <ScoreCircle examType={recentExams.exam_type} score={recentExams.total_score} />
                    ) : (
                        <p>No recent exams found</p>
                    )}
                </div>
                <div className='daily-tasks'>
                    <h2>Daily Tasks</h2>
                    <ul className='tasks'>
                        {userTasks && userTasks.map((task, index) => (
                            // text, completed, onToggleComplete
                            <TaskComponent key={index} text={task.task_title} completed={task.is_completed} onToggleComplete={() => {}} />
                        ))}
                    </ul>
                </div>
                <div className='survival_leaderboard'>
                    <h2>Survival Leaderboard</h2>
                    <div className='leaderboard'>
                        <div className='leaderboard_sort_buttons'>
                            buttons
                        </div>
                    </div>
                </div>
            </div>

            {/* Bottom content is for previous exam scores */}
            <div className='bottom-content'>
                {/* show schools Safety/Target/Reach */}
                <SchoolScroller previousScore={recentExams?.total_score} />
            </div>
        </div>
    )
}