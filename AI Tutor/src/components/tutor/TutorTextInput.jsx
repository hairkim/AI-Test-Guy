import PropTypes from 'prop-types';

export default function TutorTextInput({
    isLoading,
    onChange,
    onKeyDown,
    onSubmit,
    placeholder = 'Ask me anything...',
    value,
}) {
    return (
        <div className="input-wrapper">
            <textarea
                className="prompt auto-resize"
                value={value}
                onChange={(event) => onChange(event.target.value)}
                onKeyDown={onKeyDown}
                placeholder={placeholder}
                disabled={isLoading}
                rows={1}
            />
            <button
                className="submit-button"
                onClick={onSubmit}
                disabled={isLoading || !value.trim()}
            >
                {isLoading ? '⏳' : '➤'}
            </button>
        </div>
    );
}

TutorTextInput.propTypes = {
    isLoading: PropTypes.bool.isRequired,
    onChange: PropTypes.func.isRequired,
    onKeyDown: PropTypes.func.isRequired,
    onSubmit: PropTypes.func.isRequired,
    placeholder: PropTypes.string,
    value: PropTypes.string.isRequired,
};
