import PropTypes from 'prop-types';

export default function SurvivalErrorState({ message, onRetry }) {
    return (
        <div className="survival-error-state">
            <h2>Survival mode could not continue</h2>
            <p>{message}</p>
            <button onClick={onRetry}>Back to Survival</button>
        </div>
    );
}

SurvivalErrorState.propTypes = {
    message: PropTypes.string.isRequired,
    onRetry: PropTypes.func.isRequired,
};
