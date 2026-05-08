import PropTypes from 'prop-types';

export default function PracticeNoQuestions({ onBackToPractice }) {
    return (
        <div className="practice-empty-state">
            <h2>No practice questions loaded</h2>
            <p>
                Questions were not available for this session. This can happen if the request failed,
                your internet connection dropped, or this page was opened directly without starting
                from the practice screen.
            </p>
            <button onClick={onBackToPractice}>Back to Practice</button>
        </div>
    );
}

PracticeNoQuestions.propTypes = {
    onBackToPractice: PropTypes.func.isRequired,
};
