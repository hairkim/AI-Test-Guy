import PropTypes from 'prop-types';
import SatQuestion from '../questions/SatQuestion.jsx';
import ExamTimer from '../timers/ExamTimer.jsx';
import IntermissionTimer from '../timers/IntermissionTimer.jsx';
import TimerWarning from './TimerWarning.jsx';
import { useSingleSectionExam } from '../../hooks/useSingleSectionExam.js';

export default function SingleSectionExamPage({
    examType,
    sectionType,
    moduleStatePrefix,
    timerField,
    copy,
    classNames,
}) {
    const exam = useSingleSectionExam({
        examType,
        sectionType,
        moduleStatePrefix,
        timerField,
    });

    const currentQuestion = exam.questions[exam.currentIndex];
    const isActive = exam.activeStates.includes(exam.testState);

    return (
        <div className={classNames.root}>
            {exam.testState === 'idle' && (
                <div className={classNames.idleContainer}>
                    <div className={classNames.idleText}>
                        <h2>{copy.title}</h2>
                        {copy.description.map((line) => (
                            <p key={line}>{line}</p>
                        ))}
                    </div>
                    <div className={classNames.idleButton}>
                        <button onClick={exam.startTest} disabled={exam.isLoading}>Start Test</button>
                    </div>
                </div>
            )}

            {isActive && currentQuestion && (
                <div className={classNames.testContainer}>
                    <div className={classNames.sectionInfo}>
                        <h2>Section: {sectionType} - Module {exam.module}</h2>
                        <div className={classNames.timerContainer}>
                            <ExamTimer
                                timeLimit={exam.timer}
                                isActive={isActive}
                                onTimeUp={exam.handleTimeUp}
                                module={exam.module}
                                onWarning={() => exam.showTimerWarning('Time is running out!')}
                            />
                            <TimerWarning message={exam.timerWarning} />
                            <button
                                className={classNames.submitButton}
                                onClick={exam.submitTest}
                                disabled={exam.questions.length !== Object.keys(exam.userAnswer).length}
                            >
                                Submit Module
                            </button>
                        </div>
                    </div>
                    <SatQuestion
                        question={currentQuestion}
                        index={exam.currentIndex + 1}
                        selectedAnswer={exam.userAnswer[currentQuestion.id]}
                        handleAnswerSelect={exam.handleAnswerSelect}
                    />
                    <div className={classNames.navButtons}>
                        <button onClick={exam.selectPreviousQuestion}>Previous</button>
                        <button onClick={() => exam.selectNextQuestion(exam.questions.length)}>Next</button>
                    </div>
                </div>
            )}

            {exam.testState === 'break' && (
                <IntermissionTimer
                    timeLimit={exam.intermissionTimeLimit}
                    onIntermissionEnd={exam.onIntermissionEnd}
                    currentSectionType={sectionType}
                    isLoading={exam.isLoading}
                />
            )}

            {exam.testState === 'completed' && (
                <div className={classNames.resultsContainer}>
                    <h2>Results</h2>
                    <p>Score: {exam.score}</p>
                    <p>Percentage: {exam.percentage}</p>
                    <button onClick={exam.resetToIdle}>Retake Test</button>
                </div>
            )}
        </div>
    );
}

SingleSectionExamPage.propTypes = {
    examType: PropTypes.string.isRequired,
    sectionType: PropTypes.oneOf(['Math', 'English']).isRequired,
    moduleStatePrefix: PropTypes.string.isRequired,
    timerField: PropTypes.string.isRequired,
    copy: PropTypes.shape({
        title: PropTypes.string.isRequired,
        description: PropTypes.arrayOf(PropTypes.string).isRequired,
    }).isRequired,
    classNames: PropTypes.shape({
        root: PropTypes.string.isRequired,
        idleContainer: PropTypes.string.isRequired,
        idleText: PropTypes.string.isRequired,
        idleButton: PropTypes.string.isRequired,
        testContainer: PropTypes.string.isRequired,
        sectionInfo: PropTypes.string.isRequired,
        timerContainer: PropTypes.string.isRequired,
        submitButton: PropTypes.string.isRequired,
        navButtons: PropTypes.string.isRequired,
        resultsContainer: PropTypes.string.isRequired,
    }).isRequired,
};
