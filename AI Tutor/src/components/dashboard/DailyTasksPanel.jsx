import PropTypes from 'prop-types';
import TaskComponent from '../common/TaskComponent.jsx';

export default function DailyTasksPanel({ error, isLoading, tasks }) {
    return (
        <div className="daily-tasks">
            <h2>Daily Tasks</h2>
            {isLoading ? (
                <p>Loading daily tasks...</p>
            ) : error ? (
                <p className="dashboard-widget-error">{error}</p>
            ) : tasks.length > 0 ? (
                <ul className="tasks">
                    {tasks.map((task, index) => (
                        <TaskComponent
                            key={task.id || `${task.task_title}-${index}`}
                            text={task.task_title}
                            completed={task.is_completed}
                            onToggleComplete={() => {}}
                        />
                    ))}
                </ul>
            ) : (
                <p>No daily tasks available</p>
            )}
        </div>
    );
}

DailyTasksPanel.propTypes = {
    error: PropTypes.string,
    isLoading: PropTypes.bool.isRequired,
    tasks: PropTypes.arrayOf(
        PropTypes.shape({
            id: PropTypes.string,
            task_title: PropTypes.string.isRequired,
            is_completed: PropTypes.bool,
        })
    ).isRequired,
};
