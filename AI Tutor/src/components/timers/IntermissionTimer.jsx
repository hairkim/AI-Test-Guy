import React, { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import '../../PageComponents/CSS/BreakTimer.css'

export default function IntermissionTimer({ timeLimit, onIntermissionEnd, currentSectionType, isLoading }) {
    const [timeRemaining, setTimeRemaining] = useState(timeLimit)
    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    useEffect(() => {
        const timer = setInterval(() => {
            setTimeRemaining(prev => {
                if (prev <= 1) {
                    clearInterval(timer)
                    onIntermissionEnd()
                    return 0
                }
                return prev - 1
            })
        }, 1000)

        return () => {
            clearInterval(timer)
        }
    }, [onIntermissionEnd])

    return (
        <div className="break-timer">
            <div className='break_timer_title'>
                <h1>Intermission Time</h1>
            </div>
            <div className="break_info">
                <p>You have completed the first module of the {currentSectionType} section!</p>
                <p>The next module will begin soon.</p>
            </div>
            <div className="timer-display">
                <p>Time Remaining: {formatTime(timeRemaining)}</p>
            </div>
            <button onClick={onIntermissionEnd} disabled={isLoading}>Skip Intermission</button>
        </div>
    )
}

IntermissionTimer.propTypes = {
    timeLimit: PropTypes.number.isRequired,
    onIntermissionEnd: PropTypes.func.isRequired,
    currentSectionType: PropTypes.string.isRequired,
    isLoading: PropTypes.bool.isRequired
}
