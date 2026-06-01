import PropTypes from 'prop-types';

export default function PracticeQuestionNavigation({
    currentIndex,
    questionCount,
    onPrevious,
    onNext,
}) {
    return (
        <div className="practice-question-buttons">
            <button onClick={onPrevious} disabled={currentIndex === 0}>
                Previous
            </button>
            <span className="question-counter">
                Question {currentIndex + 1} of {questionCount}
            </span>
            <button onClick={onNext} disabled={currentIndex === questionCount - 1}>
                Next
            </button>
        </div>
    );
}

PracticeQuestionNavigation.propTypes = {
    currentIndex: PropTypes.number.isRequired,
    questionCount: PropTypes.number.isRequired,
    onPrevious: PropTypes.func.isRequired,
    onNext: PropTypes.func.isRequired,
};
