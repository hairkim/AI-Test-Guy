import PropTypes from 'prop-types';

export default function SurvivalHeader({
    difficulty,
    lives,
    questionsAnswered,
    questionsCorrect,
    section,
}) {
    return (
        <div className="survival-header">
            <div className="lives-container">
                <span className="lives-label">Lives:</span>
                {[...Array(3)].map((_, index) => (
                    <span
                        key={index}
                        className={`heart ${index < lives ? 'active' : 'lost'}`}
                    >
                        {index < lives ? '❤️' : '🖤'}
                    </span>
                ))}
            </div>
            <div className="stats-container">
                <span>Score: {questionsCorrect}/{questionsAnswered}</span>
                <span className="difficulty-badge">{difficulty}</span>
                <span className="section-badge">{section}</span>
            </div>
        </div>
    );
}

SurvivalHeader.propTypes = {
    difficulty: PropTypes.string.isRequired,
    lives: PropTypes.number.isRequired,
    questionsAnswered: PropTypes.number.isRequired,
    questionsCorrect: PropTypes.number.isRequired,
    section: PropTypes.string.isRequired,
};
