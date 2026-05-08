import PropTypes from 'prop-types';

export default function SurvivalSetup({
    onBack,
    onDifficultySelect,
    onSectionSelect,
    section,
}) {
    if (!section) {
        return (
            <div className="survival_section_container">
                <h1>Choose a Section</h1>
                <div className="survival_section_button_container">
                    <button onClick={() => onSectionSelect('Math')}>Math</button>
                    <button onClick={() => onSectionSelect('English')}>English</button>
                </div>
            </div>
        );
    }

    return (
        <div className="survival_domain_main_container">
            <button onClick={onBack} className="back-button">
                ← Back
            </button>
            <div className="survival_domain_container">
                <h1>Choose Difficulty</h1>
                <div className="survival_section_button_container">
                    <button onClick={() => onDifficultySelect('Easy')}>Easy</button>
                    <button onClick={() => onDifficultySelect('Medium')}>Medium</button>
                    <button onClick={() => onDifficultySelect('Hard')}>Hard</button>
                </div>
            </div>
        </div>
    );
}

SurvivalSetup.propTypes = {
    onBack: PropTypes.func.isRequired,
    onDifficultySelect: PropTypes.func.isRequired,
    onSectionSelect: PropTypes.func.isRequired,
    section: PropTypes.string,
};
