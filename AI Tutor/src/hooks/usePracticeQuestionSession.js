import { useState } from 'react';
import { askPracticeTutor, requestPracticeStep } from '../services/practiceTutorService';

export function usePracticeQuestionSession({ questions = [], token }) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [userAnswer, setUserAnswer] = useState({});
    const [userQuestion, setUserQuestion] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [chatHistory, setChatHistory] = useState([]);

    const currentQuestion = questions[currentIndex] || null;
    const selectedAnswer = currentQuestion ? userAnswer[currentQuestion.id] : null;

    const appendChatMessage = ({ user, tutor }) => {
        setChatHistory((prev) => [
            ...prev,
            {
                user,
                tutor,
                timestamp: new Date().toISOString(),
            },
        ]);
    };

    const handleAnswerSelect = (questionId, answer) => {
        setUserAnswer((prev) => ({
            ...prev,
            [questionId]: answer,
        }));
    };

    const handleNextQuestion = () => {
        setCurrentIndex((index) => Math.min(index + 1, questions.length - 1));
        setChatHistory([]);
        setError('');
    };

    const handlePreviousQuestion = () => {
        setCurrentIndex((index) => Math.max(index - 1, 0));
        setChatHistory([]);
        setError('');
    };

    const handleTypingComplete = (messageIndex) => {
        setChatHistory((prev) => {
            const updated = [...prev];
            updated[messageIndex].status = 'complete';
            return updated;
        });
    };

    const submitPrompt = async () => {
        if (!userQuestion.trim() || !currentQuestion) return;

        setIsLoading(true);
        setError('');

        try {
            const data = await askPracticeTutor({
                questionId: currentQuestion.id,
                userQuestion,
                chatHistory,
                token,
            });

            appendChatMessage({
                user: userQuestion,
                tutor: data.response,
            });
            setUserQuestion('');
        } catch (err) {
            console.error('Error getting tutor response:', err);
            setError('Failed to get tutor response. Please check your connection and try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const requestHint = async () => {
        if (!currentQuestion) return;

        setIsLoading(true);
        setError('');

        try {
            const data = await requestPracticeStep({
                questionId: currentQuestion.id,
                stepRequested: 'hint',
                token,
            });

            appendChatMessage({
                user: 'Can you give me a hint?',
                tutor: data.content,
            });
        } catch (err) {
            console.error('Error getting hint:', err);
            setError('Failed to get hint. Please check your connection and try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const checkAnswer = async () => {
        if (!currentQuestion) return;

        if (!selectedAnswer) {
            setError('Please select an answer first.');
            return;
        }

        setIsLoading(true);
        setError('');

        try {
            const data = await requestPracticeStep({
                questionId: currentQuestion.id,
                stepRequested: 'check_answer',
                userAttempt: selectedAnswer,
                token,
            });

            appendChatMessage({
                user: `I think the answer is ${selectedAnswer}. Is that correct?`,
                tutor: data.content,
            });
        } catch (err) {
            console.error('Error checking answer:', err);
            setError('Failed to check answer. Please check your connection and try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const explainConcept = async () => {
        if (!currentQuestion) return;

        setIsLoading(true);
        setError('');

        try {
            const data = await requestPracticeStep({
                questionId: currentQuestion.id,
                stepRequested: 'explanation',
                token,
            });

            appendChatMessage({
                user: 'Can you explain the concept behind this question?',
                tutor: data.content,
            });
        } catch (err) {
            console.error('Error getting explanation:', err);
            setError('Failed to get explanation. Please check your connection and try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            submitPrompt();
        }
    };

    return {
        chatHistory,
        checkAnswer,
        currentIndex,
        currentQuestion,
        error,
        explainConcept,
        handleAnswerSelect,
        handleKeyDown,
        handleNextQuestion,
        handlePreviousQuestion,
        handleTypingComplete,
        isLoading,
        requestHint,
        selectedAnswer,
        setUserQuestion,
        submitPrompt,
        userAnswer,
        userQuestion,
    };
}
