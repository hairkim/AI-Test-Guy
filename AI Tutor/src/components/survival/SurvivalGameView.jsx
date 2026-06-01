import PropTypes from 'prop-types';
import SurvivalQuestion from '../questions/SurvivalQuestion.jsx';
import SurvivalFeedback from './SurvivalFeedback.jsx';
import SurvivalHeader from './SurvivalHeader.jsx';

export default function SurvivalGameView({
    difficulty,
    gameOver,
    lives,
    loading,
    onAnswerSelect,
    onNextQuestion,
    question,
    questionsAnswered,
    questionsCorrect,
    section,
    selectedAnswer,
    showFeedback,
}) {
    return (
        <div className="survival-questions-container">
            <SurvivalHeader
                difficulty={difficulty}
                lives={lives}
                questionsAnswered={questionsAnswered}
                questionsCorrect={questionsCorrect}
                section={section}
            />

            {question && (
                <div className="question-container">
                    <SurvivalQuestion
                        question={question}
                        index={questionsAnswered + 1}
                        selectedAnswer={selectedAnswer}
                        handleAnswerSelect={onAnswerSelect}
                        showFeedback={showFeedback}
                        correctAnswer={question.correct_answer}
                    />

                    {showFeedback && (
                        <SurvivalFeedback
                            correctAnswer={question.correct_answer}
                            explanation={question.explanation}
                            gameOver={gameOver}
                            loading={loading}
                            onNext={onNextQuestion}
                            selectedAnswer={selectedAnswer}
                        />
                    )}
                </div>
            )}
        </div>
    );
}

SurvivalGameView.propTypes = {
    difficulty: PropTypes.string.isRequired,
    gameOver: PropTypes.bool.isRequired,
    lives: PropTypes.number.isRequired,
    loading: PropTypes.bool.isRequired,
    onAnswerSelect: PropTypes.func.isRequired,
    onNextQuestion: PropTypes.func.isRequired,
    question: PropTypes.object,
    questionsAnswered: PropTypes.number.isRequired,
    questionsCorrect: PropTypes.number.isRequired,
    section: PropTypes.string.isRequired,
    selectedAnswer: PropTypes.string,
    showFeedback: PropTypes.bool.isRequired,
};
