import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext.jsx';
import { generateMockExam, submitTestModule } from '../services/satService.js';
import { useQuestionNavigator } from './useQuestionNavigator.js';
import { useTimerWarning } from './useTimerWarning.js';

export function useSingleSectionExam({ examType, sectionType, moduleStatePrefix, timerField }) {
    const { user, session } = useAuth();
    const [questions, setQuestions] = useState([]);
    const [testState, setTestState] = useState('idle');
    const [isLoading, setIsLoading] = useState(false);
    const [userAnswer, setUserAnswer] = useState({});
    const [module, setModule] = useState(1);
    const [examId, setExamId] = useState(null);
    const [score, setScore] = useState(null);
    const [percentage, setPercentage] = useState(null);
    const [timer, setTimer] = useState(0);
    const {
        currentIndex,
        resetQuestionIndex,
        selectNextQuestion,
        selectPreviousQuestion,
    } = useQuestionNavigator();
    const { timerWarning, showTimerWarning } = useTimerWarning();

    const activeStates = [`${moduleStatePrefix}1`, `${moduleStatePrefix}2`];
    const intermissionTimeLimit = 60;

    const startTest = async () => {
        setIsLoading(true);
        setUserAnswer({});

        if (!user?.id) {
            alert('Please sign in to take a test');
            setIsLoading(false);
            return;
        }

        try {
            const data = await generateMockExam({
                examType,
                userId: user.id,
                token: session.access_token,
            });

            setTimer(data[timerField]);
            setQuestions(data.questions);
            setExamId(data.exam_id);
            setModule(1);
            resetQuestionIndex();
            setTestState(`${moduleStatePrefix}1`);
        } catch (error) {
            console.error('Error loading questions:', error);
            setTestState('error');
        } finally {
            setIsLoading(false);
        }
    };

    const handleAnswerSelect = (questionId, answer) => {
        setUserAnswer((prev) => ({
            ...prev,
            [questionId]: answer,
        }));
    };

    const handleTimeUp = () => {
        console.log('Time is up, submitting test');
        // submitTest()
    };

    const onIntermissionEnd = () => {
        setTestState(`${moduleStatePrefix}2`);
    };

    const submitTest = async () => {
        if (!examId) {
            console.error('No exam ID found');
            return;
        }

        setIsLoading(true);
        console.log('submitting test');
        setTestState(module === 1 ? 'break' : 'completed');

        try {
            const data = await submitTestModule({
                sectionType,
                module,
                examId,
                answers: userAnswer,
                timeEnded: module === 2 ? new Date().toISOString() : null,
                token: session.access_token,
            });
            console.log('Submit response:', data);

            if (module === 1) {
                setQuestions(data.module2_questions);
                setModule(2);
                resetQuestionIndex();
                setUserAnswer({});
            } else {
                setScore(data.section_score);
                setPercentage(data.percentage);
            }
        } catch (error) {
            console.error('Error submitting test:', error);
            setTestState('error');
        } finally {
            setIsLoading(false);
        }
    };

    const resetToIdle = () => {
        setTestState('idle');
    };

    return {
        activeStates,
        currentIndex,
        examId,
        handleAnswerSelect,
        handleTimeUp,
        intermissionTimeLimit,
        isLoading,
        module,
        onIntermissionEnd,
        percentage,
        questions,
        resetToIdle,
        score,
        selectNextQuestion,
        selectPreviousQuestion,
        showTimerWarning,
        startTest,
        submitTest,
        testState,
        timer,
        timerWarning,
        userAnswer,
    };
}
