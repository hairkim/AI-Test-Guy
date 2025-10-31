import React from 'react'
import '../CSS/SurvivalModeQuestions.css'
import PropTypes from 'prop-types'

export default function GameOver({ questionsAnswered, questionsCorrect, handlePlayAgain }) {
    return (
        <div className="game-over-container">
            <h1>Game Over! 💀</h1>
            <div className="final-stats">
                <h2>Final Stats</h2>
                <p>Questions Answered: {questionsAnswered}</p>
                <p>Questions Correct: {questionsCorrect}</p>
                <p>Accuracy: {questionsAnswered > 0 ? ((questionsCorrect / questionsAnswered) * 100).toFixed(1) : 0}%</p>
            </div>
            <button onClick={handlePlayAgain} className="play-again-button">
                Play Again
            </button>
        </div>
    )
}

GameOver.propTypes = {
    questionsAnswered: PropTypes.number.isRequired,
    questionsCorrect: PropTypes.number.isRequired,
    handlePlayAgain: PropTypes.func.isRequired,
}
