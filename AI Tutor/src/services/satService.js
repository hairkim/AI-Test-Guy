import { apiRequest } from './apiClient';

export const getRandomQuestions = ({ section, count, difficulty, domain, token }) => (
    apiRequest('/api/sat/questions/random', {
        token,
        queryParams: { section, count, difficulty, domain },
    })
);

export const generateMockExam = ({ examType, userId, token }) => (
    apiRequest('/api/sat/mock-exam/generate', {
        method: 'POST',
        token,
        body: {
            exam_type: examType,
            user_id: userId,
            started_at: new Date().toISOString(),
        },
    })
);

export const getMockExamHistory = ({ token }) => (
    apiRequest('/api/sat/mock-exam/history', { token })
);

export const submitTestModule = ({ sectionType, module, examId, answers, timeEnded, token }) => {
    const body = {
        exam_id: examId,
        answers,
        module,
    };

    if (timeEnded) {
        body.time_ended = timeEnded;
    }

    return apiRequest(`/api/sat/submit_test/${sectionType}/${module}`, {
        method: 'POST',
        token,
        body,
    });
};

export const getExamSectionModule = ({ sectionType, moduleNumber, examId, token }) => (
    apiRequest(`/api/sat/mock-exam/section/${sectionType}/module/${moduleNumber}`, {
        token,
        headers: {
            'X-Exam-ID': examId,
        },
    })
);

export const getCollegeRecommendations = ({ score, safetyLimit, targetLimit, reachLimit }) => (
    apiRequest(`/api/sat/colleges/recommendations/${score}`, {
        queryParams: {
            safety_limit: safetyLimit,
            target_limit: targetLimit,
            reach_limit: reachLimit,
        },
    })
);
