import { useCallback, useEffect, useState } from 'react';
import { getSurvivalQuestion, saveSurvivalSession } from '../services/survivalService';

const INITIAL_LIVES = 3;

export function useSurvivalSession({ difficulty, section, userId }) {
    const [lives, setLives] = useState(INITIAL_LIVES);
    const [currentQuestion, setCurrentQuestion] = useState(null);
    const [excludedQuestionIds, setExcludedQuestionIds] = useState([]);
    const [selectedAnswer, setSelectedAnswer] = useState(null);
    const [showFeedback, setShowFeedback] = useState(false);
    const [loading, setLoading] = useState(false);
    const [gameOver, setGameOver] = useState(false);
    const [startingTime, setStartingTime] = useState(null);
    const [questionsAnswered, setQuestionsAnswered] = useState(0);
    const [questionsCorrect, setQuestionsCorrect] = useState(0);
    const [answers, setAnswers] = useState([]);
    const [error, setError] = useState('');

    const saveSession = useCallback(async ({
        finalAnswers,
        finalExcludedQuestionIds,
        finalQuestionsAnswered,
        finalQuestionsCorrect,
    }) => {
        if (!userId || !startingTime) return;

        try {
            const result = await saveSurvivalSession({
                userId,
                difficulty,
                section,
                questionsAnswered: finalQuestionsAnswered,
                questionsCorrect: finalQuestionsCorrect,
                questionIds: finalExcludedQuestionIds,
                answers: finalAnswers,
                startTime: startingTime,
            });

            console.log('Session saved:', result);
        } catch (err) {
            console.error('Error saving survival session:', err);
            setError('Could not save your survival session. You can go back and retry survival mode.');
        }
    }, [difficulty, section, startingTime, userId]);

    const fetchQuestion = useCallback(async () => {
        if (gameOver) return;

        setLoading(true);
        setError('');

        try {
            const question = await getSurvivalQuestion({
                difficulty,
                section,
                excludedQuestionIds,
            });

            setCurrentQuestion(question);
            setSelectedAnswer(null);
            setShowFeedback(false);
        } catch (err) {
            console.error('Error fetching survival question:', err);
            setError(
                err.message.includes('No more questions')
                    ? 'No more questions are available for this section and difficulty.'
                    : 'Error loading question. Please check your connection and try again.'
            );
        } finally {
            setLoading(false);
        }
    }, [difficulty, excludedQuestionIds, gameOver, section]);

    useEffect(() => {
        if (!section || !difficulty) return;

        let isMounted = true;
        setStartingTime(new Date().toISOString());

        const fetchInitialQuestion = async () => {
            setLoading(true);
            setError('');

            try {
                const question = await getSurvivalQuestion({
                    difficulty,
                    section,
                    excludedQuestionIds: [],
                });

                if (isMounted) {
                    setCurrentQuestion(question);
                    setSelectedAnswer(null);
                    setShowFeedback(false);
                }
            } catch (err) {
                console.error('Error fetching survival question:', err);
                if (isMounted) {
                    setError(
                        err.message.includes('No more questions')
                            ? 'No more questions are available for this section and difficulty.'
                            : 'Error loading question. Please check your connection and try again.'
                    );
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };

        fetchInitialQuestion();

        return () => {
            isMounted = false;
        };
    }, [section, difficulty]);

    const handleAnswerSelect = (questionId, answer) => {
        if (showFeedback || !currentQuestion) return;

        // TODO: Move survival answer validation back to the backend so the frontend
        // does not need the correct answer before the user responds.
        const isCorrect = answer === currentQuestion.correct_answer;
        const nextLives = isCorrect ? lives : lives - 1;
        const nextQuestionsAnswered = questionsAnswered + 1;
        const nextQuestionsCorrect = isCorrect ? questionsCorrect + 1 : questionsCorrect;
        const answerRecord = {
            question_id: questionId,
            user_answer: answer,
            correct_answer: currentQuestion.correct_answer,
            is_correct: isCorrect,
        };
        const nextAnswers = [...answers, answerRecord];
        const nextExcludedQuestionIds = [...excludedQuestionIds, questionId];

        setSelectedAnswer(answer);
        setShowFeedback(true);
        setQuestionsAnswered(nextQuestionsAnswered);
        setQuestionsCorrect(nextQuestionsCorrect);
        setAnswers(nextAnswers);
        setExcludedQuestionIds(nextExcludedQuestionIds);

        if (!isCorrect) {
            setLives(nextLives);
        }

        if (!isCorrect && nextLives <= 0) {
            setGameOver(true);
            setTimeout(() => {
                saveSession({
                    finalAnswers: nextAnswers,
                    finalExcludedQuestionIds: nextExcludedQuestionIds,
                    finalQuestionsAnswered: nextQuestionsAnswered,
                    finalQuestionsCorrect: nextQuestionsCorrect,
                });
            }, 1500);
        }
    };

    const handleNextQuestion = () => {
        if (gameOver) return;
        fetchQuestion();
    };

    return {
        currentQuestion,
        difficulty,
        error,
        gameOver,
        handleAnswerSelect,
        handleNextQuestion,
        lives,
        loading,
        questionsAnswered,
        questionsCorrect,
        section,
        selectedAnswer,
        showFeedback,
    };
}
