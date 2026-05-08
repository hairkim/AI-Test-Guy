import PropTypes from 'prop-types';

export default function TimerWarning({ message }) {
    if (!message) {
        return null;
    }

    return (
        <div style={{
            position: 'fixed',
            top: '100px',
            right: '20px',
            backgroundColor: '#FEF3C7',
            border: '1px solid #F59E0B',
            borderRadius: '6px',
            padding: '8px 12px',
            fontSize: '14px',
            color: '#92400E',
            zIndex: 1001
        }}>
            {message}
        </div>
    );
}

TimerWarning.propTypes = {
    message: PropTypes.string,
};
