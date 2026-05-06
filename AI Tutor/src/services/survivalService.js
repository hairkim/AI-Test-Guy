import { apiRequest } from './apiClient';

export const getSurvivalQuestion = ({ difficulty, section, excludedQuestionIds, domain }) => (
    apiRequest('/api/survival/question', {
        method: 'POST',
        body: {
            difficulty,
            section,
            domain,
            excluded_question_ids: excludedQuestionIds,
        },
    })
);

export const saveSurvivalSession = ({
    userId,
    difficulty,
    section,
    questionsAnswered,
    questionsCorrect,
    questionIds,
    answers,
    startTime,
}) => (
    apiRequest('/api/survival/session/save', {
        method: 'POST',
        body: {
            user_id: userId,
            difficulty,
            section,
            questions_answered: questionsAnswered,
            questions_correct: questionsCorrect,
            question_ids: questionIds,
            answers,
            start_time: startTime,
        },
    })
);

export const getSurvivalLeaderboard = ({ section, difficulty, limit = 20 }) => (
    apiRequest('/api/survival/leaderboard', {
        queryParams: { section, difficulty, limit },
    })
);
