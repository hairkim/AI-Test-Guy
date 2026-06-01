import PropTypes from 'prop-types';

export default function TutorErrorRecovery({ error, onBackHome }) {
    if (!error) {
        return null;
    }

    return (
        <div className="error-message">
            <p>{error}</p>
            <button type="button" onClick={onBackHome}>
                Back to Home
            </button>
        </div>
    );
}

TutorErrorRecovery.propTypes = {
    error: PropTypes.string.isRequired,
    onBackHome: PropTypes.func.isRequired,
};
