import React from 'react'
import PropTypes from 'prop-types'
import '../CSS/BreakTimer.css'

export default function IntermissionTimer({ timeRemaining, onIntermissionEnd, currentSectionType }) {
    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }

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
            <button onClick={onIntermissionEnd}>Skip Intermission</button>
        </div>
    )
}

IntermissionTimer.propTypes = {
    timeRemaining: PropTypes.number.isRequired,
    onIntermissionEnd: PropTypes.func.isRequired,
    currentSectionType: PropTypes.string.isRequired
}
