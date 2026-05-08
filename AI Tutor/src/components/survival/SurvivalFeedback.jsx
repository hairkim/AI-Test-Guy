import PropTypes from 'prop-types';

export default function SurvivalFeedback({
    correctAnswer,
    explanation,
    gameOver,
    loading,
    onNext,
    selectedAnswer,
}) {
    const isCorrect = selectedAnswer === correctAnswer;

    return (
        <div className="feedback-section">
            {isCorrect ? (
                <div className="correct-message">
                    <span className="icon">✅</span>
                    <h3>Correct!</h3>
                </div>
            ) : (
                <div className="incorrect-message">
                    <span className="icon">❌</span>
                    <h3>Wrong!</h3>
                    <p className="correct-answer-text">
                        The correct answer was: <strong>{correctAnswer}</strong>
                    </p>
                    {explanation && (
                        <div className="explanation">
                            <h4>Explanation:</h4>
                            <p>{explanation}</p>
                        </div>
                    )}
                </div>
            )}

            {!gameOver && (
                <button
                    onClick={onNext}
                    className="next-button"
                    disabled={loading}
                >
                    {loading ? 'Loading...' : 'Next Question →'}
                </button>
            )}
        </div>
    );
}

SurvivalFeedback.propTypes = {
    correctAnswer: PropTypes.string.isRequired,
    explanation: PropTypes.string,
    gameOver: PropTypes.bool.isRequired,
    loading: PropTypes.bool.isRequired,
    onNext: PropTypes.func.isRequired,
    selectedAnswer: PropTypes.string,
};
