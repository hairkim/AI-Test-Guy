import { apiRequest } from './apiClient';

export const askPracticeTutor = ({ questionId, userQuestion, chatHistory, token }) => (
    apiRequest('/api/practice-tutor/ask', {
        method: 'POST',
        token,
        body: {
            question_id: questionId,
            user_question: userQuestion,
            chat_history: chatHistory,
        },
    })
);

export const requestPracticeStep = ({ questionId, stepRequested, userAttempt, token }) => (
    apiRequest('/api/practice-tutor/step', {
        method: 'POST',
        token,
        body: {
            question_id: questionId,
            step_requested: stepRequested,
            user_attempt: userAttempt,
        },
    })
);
