import React, { useState, useEffect, useRef } from 'react'
import PropTypes from 'prop-types'

const ExamTimer = ({ 
    timeLimit, // in minutes
    isActive, 
    onTimeUp, 
    module,
    onWarning = null 
}) => {
    const [timeRemaining, setTimeRemaining] = useState(timeLimit * 60)
    const [isRunning, setIsRunning] = useState(false)
    const intervalRef = useRef(null)
    const warningShownRef = useRef(false)

    // Helper function to clear the timer
    const clearTimer = () => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current)
            intervalRef.current = null
        }
        setIsRunning(false)
    }

    // Start/stop timer based on isActive prop - FIXED
    useEffect(() => {
        if (isActive) {
            startTimer()
        } else {
            clearTimer()
        }
    }, [isActive]) // Remove isRunning from dependencies

    // Reset timer when timeLimit changes
    useEffect(() => {
        setTimeRemaining(timeLimit * 60)
        warningShownRef.current = false
        clearTimer()
        
        if (isActive) {
            startTimer()
        }
    }, [timeLimit]) // Remove isActive from dependencies since it's handled above

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            clearTimer()
        }
    }, [])

    const startTimer = () => {
        clearTimer() // Clear any existing timer
        
        setIsRunning(true)
        intervalRef.current = setInterval(() => {
            setTimeRemaining(prev => {
                const newTime = prev - 1

                if (newTime === 300 && !warningShownRef.current && onWarning) {
                    warningShownRef.current = true
                    onWarning("5 minutes remaining!")
                }

                if (newTime <= 0) {
                    clearTimer()
                    onTimeUp()
                    return 0
                }

                return newTime
            })
        }, 1000)
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