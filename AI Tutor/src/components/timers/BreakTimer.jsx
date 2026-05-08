import React, { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import '../../PageComponents/CSS/BreakTimer.css'

export default function BreakTimer({ timeLimit, onBreakEnd, isLoading }) {
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
                    onBreakEnd()
                    return 0
                }
                return prev - 1
            })
        }, 1000)

        return () => {
            clearInterval(timer)
        }
    }, [onBreakEnd])

    return (
        <div className="break-timer">
            <div className='break_timer_title'>
                <h1>Break Time</h1>
            </div>
            <div className="break_info">
                <p>You have completed the English section!</p>
                <p>Take a break before starting the Math section.</p>
                <p>The break will end automatically, or you can skip it.</p>
            </div>
            <div className="timer-display">
                <p>Time Remaining: {formatTime(timeRemaining)}</p>
            </div>
            <button onClick={() => onBreakEnd()} disabled={isLoading}>Skip Break</button>
        </div>
    )
}

BreakTimer.propTypes = {
    timeLimit: PropTypes.number.isRequired,
    onBreakEnd: PropTypes.func.isRequired,
    isLoading: PropTypes.bool.isRequired
}
