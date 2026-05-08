import { useEffect, useState } from 'react';
import { generateDailyTasks } from '../services/dailyTaskService.js';
import { getMockExamHistory } from '../services/satService.js';

const getMostRecentCompletedExam = (exams) => {
    const completedExams = exams.filter((exam) => exam.completed_at !== null);

    if (completedExams.length === 0) {
        return null;
    }

    return completedExams.sort((a, b) => new Date(b.completed_at) - new Date(a.completed_at))[0];
};

export function useDashboardData(session) {
    const [recentExam, setRecentExam] = useState(null);
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState({
        recentExam: false,
        tasks: false,
    });
    const [errors, setErrors] = useState({
        recentExam: '',
        tasks: '',
    });

    useEffect(() => {
        const token = session?.access_token;

        if (!token) {
            setRecentExam(null);
            setTasks([]);
            setErrors({ recentExam: '', tasks: '' });
            setLoading({ recentExam: false, tasks: false });
            return;
        }

        const loadRecentExam = async () => {
            setLoading((prev) => ({ ...prev, recentExam: true }));
            setErrors((prev) => ({ ...prev, recentExam: '' }));

            try {
                const exams = await getMockExamHistory({ token });
                setRecentExam(getMostRecentCompletedExam(exams));
            } catch (error) {
                console.error('Error fetching recent exams:', error);
                setRecentExam(null);
                setErrors((prev) => ({
                    ...prev,
                    recentExam: 'Unable to load your recent exam score.',
                }));
            } finally {
                setLoading((prev) => ({ ...prev, recentExam: false }));
            }
        };

        const loadDailyTasks = async () => {
            setLoading((prev) => ({ ...prev, tasks: true }));
            setErrors((prev) => ({ ...prev, tasks: '' }));

            try {
                const response = await generateDailyTasks({ token });
                setTasks(response.tasks || []);
            } catch (error) {
                console.error('Error fetching tasks:', error);
                setTasks([]);
                setErrors((prev) => ({
                    ...prev,
                    tasks: 'Unable to load daily tasks.',
                }));
            } finally {
                setLoading((prev) => ({ ...prev, tasks: false }));
            }
        };

        loadRecentExam();
        loadDailyTasks();
    }, [session?.access_token]);

    return {
        errors,
        loading,
        recentExam,
        tasks,
    };
}
