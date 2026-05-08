import PropTypes from 'prop-types';

export default function PracticeQuickActions({
    isLoading,
    hasSelectedAnswer,
    onHint,
    onCheckAnswer,
    onExplainConcept,
}) {
    return (
        <div className="quick-actions">
            <button
                onClick={onHint}
                disabled={isLoading}
                className="quick-action-btn hint-btn"
            >
                💡 Get Hint
            </button>
            <button
                onClick={onCheckAnswer}
                disabled={isLoading || !hasSelectedAnswer}
                className="quick-action-btn check-btn"
            >
                ✓ Check Answer
            </button>
            <button
                onClick={onExplainConcept}
                disabled={isLoading}
                className="quick-action-btn explain-btn"
            >
                📚 Explain Concept
            </button>
        </div>
    );
}

PracticeQuickActions.propTypes = {
    isLoading: PropTypes.bool.isRequired,
    hasSelectedAnswer: PropTypes.bool.isRequired,
    onHint: PropTypes.func.isRequired,
    onCheckAnswer: PropTypes.func.isRequired,
    onExplainConcept: PropTypes.func.isRequired,
};
