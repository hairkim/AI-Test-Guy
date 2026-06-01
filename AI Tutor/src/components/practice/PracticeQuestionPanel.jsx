import PropTypes from 'prop-types';
import SatQuestion from '../questions/SatQuestion.jsx';
import PracticeQuestionNavigation from './PracticeQuestionNavigation.jsx';
import PracticeQuickActions from './PracticeQuickActions.jsx';

export default function PracticeQuestionPanel({
    currentIndex,
    question,
    questionCount,
    selectedAnswer,
    isLoading,
    onAnswerSelect,
    onPrevious,
    onNext,
    onHint,
    onCheckAnswer,
    onExplainConcept,
}) {
    return (
        <div className="question_container">
            <div className="thesatquestioncontainer">
                <SatQuestion
                    key={question.id}
                    question={question}
                    index={currentIndex + 1}
                    selectedAnswer={selectedAnswer}
                    handleAnswerSelect={onAnswerSelect}
                />
            </div>
            <PracticeQuestionNavigation
                currentIndex={currentIndex}
                questionCount={questionCount}
                onPrevious={onPrevious}
                onNext={onNext}
            />
            <PracticeQuickActions
                isLoading={isLoading}
                hasSelectedAnswer={!!selectedAnswer}
                onHint={onHint}
                onCheckAnswer={onCheckAnswer}
                onExplainConcept={onExplainConcept}
            />
        </div>
    );
}

PracticeQuestionPanel.propTypes = {
    currentIndex: PropTypes.number.isRequired,
    question: PropTypes.object.isRequired,
    questionCount: PropTypes.number.isRequired,
    selectedAnswer: PropTypes.string,
    isLoading: PropTypes.bool.isRequired,
    onAnswerSelect: PropTypes.func.isRequired,
    onPrevious: PropTypes.func.isRequired,
    onNext: PropTypes.func.isRequired,
    onHint: PropTypes.func.isRequired,
    onCheckAnswer: PropTypes.func.isRequired,
    onExplainConcept: PropTypes.func.isRequired,
};
