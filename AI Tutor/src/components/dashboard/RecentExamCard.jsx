import PropTypes from 'prop-types';
import ScoreCircle from './ScoreCircle.jsx';

export default function RecentExamCard({ error, isLoading, recentExam }) {
    return (
        <div className="most-recent-exam">
            <h2>Most Recent Exam Score</h2>
            {isLoading ? (
                <p>Loading recent exam...</p>
            ) : error ? (
                <p className="dashboard-widget-error">{error}</p>
            ) : recentExam ? (
                <ScoreCircle examType={recentExam.exam_type} score={recentExam.total_score} />
            ) : (
                <p>No recent exams found</p>
            )}
        </div>
    );
}

RecentExamCard.propTypes = {
    error: PropTypes.string,
    isLoading: PropTypes.bool.isRequired,
    recentExam: PropTypes.shape({
        exam_type: PropTypes.string.isRequired,
        total_score: PropTypes.number.isRequired,
    }),
};
