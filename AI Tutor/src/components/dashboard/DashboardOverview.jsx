import PropTypes from 'prop-types';
import DailyTasksPanel from './DailyTasksPanel.jsx';
import RecentExamCard from './RecentExamCard.jsx';

export default function DashboardOverview({
    errors,
    loading,
    recentExam,
    tasks,
}) {
    return (
        <div className="exams-tasks">
            <RecentExamCard
                error={errors.recentExam}
                isLoading={loading.recentExam}
                recentExam={recentExam}
            />
            <DailyTasksPanel
                error={errors.tasks}
                isLoading={loading.tasks}
                tasks={tasks}
            />
        </div>
    );
}

DashboardOverview.propTypes = {
    errors: PropTypes.shape({
        recentExam: PropTypes.string,
        tasks: PropTypes.string,
    }).isRequired,
    loading: PropTypes.shape({
        recentExam: PropTypes.bool.isRequired,
        tasks: PropTypes.bool.isRequired,
    }).isRequired,
    recentExam: PropTypes.object,
    tasks: PropTypes.array.isRequired,
};
