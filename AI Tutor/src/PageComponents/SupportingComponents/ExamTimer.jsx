import React, { useState, useEffect, useRef } from 'react'
import PropTypes from 'prop-types'

const ExamTimer = ({ 
    timeLimit, // in minutes
    isActive, 
    onTimeUp, 
    module,
    onWarning = null // optional callback for warnings
}) => {
    const [timeRemaining, setTimeRemaining] = useState(timeLimit * 60) // convert to seconds
    const [isRunning, setIsRunning] = useState(false)
    const intervalRef = useRef(null)
    const warningShownRef = useRef(false)

    // Start/stop timer based on isActive prop
    useEffect(() => {
        if (isActive && !isRunning) {
            startTimer()
        } else if (!isActive && isRunning) {
            pauseTimer()
        }
    }, [isActive])

    // Reset timer when timeLimit changes (new module)
    useEffect(() => {
        setTimeRemaining(timeLimit * 60)
        warningShownRef.current = false
        if (isActive) {
            startTimer()
        }
    }, [timeLimit])

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    }, [])

    const startTimer = () => {
        setIsRunning(true)
        intervalRef.current = setInterval(() => {
            setTimeRemaining(prev => {
                const newTime = prev - 1

                // Show warning at 5 minutes remaining
                if (newTime === 300 && !warningShownRef.current && onWarning) {
                    warningShownRef.current = true
                    onWarning("5 minutes remaining!")
                }

                // Time's up
                if (newTime <= 0) {
                    clearInterval(intervalRef.current)
                    setIsRunning(false)
                    onTimeUp() // Auto-submit
                    return 0
                }

                return newTime
            })
        }, 1000)
    }

    const pauseTimer = () => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current)
        }
        setIsRunning(false)
    }

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const getTimerColor = () => {
        if (timeRemaining <= 300) return '#EF4444' // Red for last 5 minutes
        if (timeRemaining <= 600) return '#F59E0B' // Yellow for last 10 minutes
        return '#10B981' // Green
    }

    return (
        <div style={{
            position: 'fixed',
            top: '20px',
            right: '20px',
            backgroundColor: 'white',
            border: `2px solid ${getTimerColor()}`,
            borderRadius: '8px',
            padding: '12px 16px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            zIndex: 1000
        }}>
            <div style={{ 
                fontSize: '14px', 
                fontWeight: '600', 
                color: '#374151',
                marginBottom: '4px'
            }}>
                Module {module} Time
            </div>
            <div style={{ 
                fontSize: '20px', 
                fontWeight: 'bold', 
                color: getTimerColor(),
                textAlign: 'center'
            }}>
                {formatTime(timeRemaining)}
            </div>
            {!isRunning && isActive && (
                <div style={{ fontSize: '12px', color: '#6B7280' }}>
                    Paused
                </div>
            )}
        </div>
    )
}

export default ExamTimer

ExamTimer.propTypes = {
    timeLimit: PropTypes.number.isRequired,
    isActive: PropTypes.bool.isRequired,
    onTimeUp: PropTypes.func.isRequired,
    module: PropTypes.number.isRequired,
    onWarning: PropTypes.func
};
