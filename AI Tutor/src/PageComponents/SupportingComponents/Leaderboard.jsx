import React, { useState, useEffect } from 'react'
import Select from 'react-select'
import '../CSS/Leaderboard.css'
import LeaderboardEntry from './LeaderboardEntry.jsx'

export default function SurvivalLeaderboard() {
    const [section, setSection] = useState('Math')
    const [difficulty, setDifficulty] = useState('Easy')
    const [leaderboard, setLeaderboard] = useState([])

    useEffect(() => {
        const loadLeaderboard = async () => {
            const leaderboard = await fetchLeaderboard()
            console.log("leaderboard:", leaderboard)
            setLeaderboard(leaderboard)
        }
        loadLeaderboard()
    }, [section, difficulty])

    const BACKEND_URL = import.meta.env.VITE_BACKEND_PORT

    const fetchLeaderboard = async () => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/survival/leaderboard?section=${section}&difficulty=${difficulty}&limit=20`)
            const data = await response.json()
            return data.leaderboard
        } catch (error) {
            console.error('Error fetching leaderboard:', error)
        }
    }

    const sections = [
        { value: 'math', label: 'Math' },
        { value: 'english', label: 'English' }
    ]

    const difficulties = [
        { value: 'easy', label: 'Easy' },
        { value: 'medium', label: 'Medium' },
        { value: 'hard', label: 'Hard' }
    ]

    return (
        <div>
            <h2>Survival Leaderboard</h2>
            <div className='survival_leaderboard_buttons'>
                <Select 
                options={sections} 
                onChange={(e) => setSection(e.value)} 
                classNamePrefix='custom_select'
                value={sections.find(opt => opt.label === section)}
                />
                <Select 
                options={difficulties} 
                onChange={(e) => setDifficulty(e.value)} 
                classNamePrefix='custom_select'
                value={difficulties.find(opt => opt.label === difficulty)}
                />
            </div>
            <div className='survival_leaderboard_content'>
                {leaderboard.map((entry) => (
                    <LeaderboardEntry key={entry.user_id} entry={entry} />
                ))}
            </div>
        </div>
    )
}