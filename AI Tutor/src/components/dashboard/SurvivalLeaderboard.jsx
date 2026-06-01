import React, { useState, useEffect } from 'react'
import Select from 'react-select'
import '../../PageComponents/CSS/Leaderboard.css'
import LeaderboardEntry from './LeaderboardEntry.jsx'
import { getSurvivalLeaderboard } from '../../services/survivalService.js'

export default function SurvivalLeaderboard() {
    const [section, setSection] = useState('Math')
    const [difficulty, setDifficulty] = useState('Easy')
    const [leaderboard, setLeaderboard] = useState([])
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState('')

    useEffect(() => {
        const loadLeaderboard = async () => {
            setIsLoading(true)
            setError('')

            try {
                const data = await getSurvivalLeaderboard({ section, difficulty, limit: 20 })
                const entries = data.leaderboard || []
                console.log("leaderboard:", entries)
                setLeaderboard(entries)
            } catch (requestError) {
                console.error('Error fetching leaderboard:', requestError)
                setLeaderboard([])
                setError('Unable to load survival leaderboard.')
            } finally {
                setIsLoading(false)
            }
        }

        loadLeaderboard()
    }, [section, difficulty])

    const sections = [
        { value: 'Math', label: 'Math' },
        { value: 'English', label: 'English' }
    ]

    const difficulties = [
        { value: 'Easy', label: 'Easy' },
        { value: 'Medium', label: 'Medium' },
        { value: 'Hard', label: 'Hard' }
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
                {isLoading && <p>Loading leaderboard...</p>}
                {!isLoading && error && <p className="dashboard-widget-error">{error}</p>}
                {!isLoading && !error && leaderboard.length === 0 && (
                    <p>No leaderboard entries yet</p>
                )}
                {!isLoading && !error && leaderboard.map((entry) => (
                    <LeaderboardEntry key={entry.user_id} entry={entry} />
                ))}
            </div>
        </div>
    )
}
