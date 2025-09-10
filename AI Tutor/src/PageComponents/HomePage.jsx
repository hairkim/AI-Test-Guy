import React from 'react';
import ProfilePicture from './ProfilePicture.jsx'
import TaskComponent from './TaskComponent.jsx'
import './HomePage.css'
import { useAuth } from '../ClientStuff/AuthContext.jsx'
import { useProtectedNavigation } from '../ClientStuff/UserProtectedNav.js'

export default function HomePage() {
    const { navigateWithAuth } = useProtectedNavigation()
    const { user } = useAuth();
    const pages = ['Practice Exam', 'Practice Questions', 'Ask TutorGuy', 'Exam History']
    const tasks = ['Daily 5 Math Questions','Daily 5 English Questions','Take a Practice Exam']
    const pageRoute = (page) => {
        switch (page) {
            case 'Practice Exam':
                navigateWithAuth('/take_a_test')
                break;
            case 'Practice Questions':
                navigateWithAuth('/math_test') // make new route later
                break;
            case 'Ask TutorGuy':
                navigateWithAuth('/query')
                break;
            case 'Exam History':
                navigateWithAuth('/exam_history')
                break;
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