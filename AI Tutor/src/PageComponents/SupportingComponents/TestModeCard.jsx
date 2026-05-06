import React from 'react';
import PropTypes from 'prop-types';
import '../CSS/TestModeCard.css';

export default function TestModeCard({ icon, title, description, onStart }) {
    return (
        <div className="tmc-card">
            <div className="tmc-image">
                <span className="tmc-icon">{icon}</span>
            </div>
            <div className="tmc-body">
                <h3 className="tmc-title">{title}</h3>
                <p className="tmc-description">{description}</p>
                <button className="tmc-start-btn" onClick={onStart}>
                    Start
                </button>
            </div>
        </div>
    );
}

TestModeCard.propTypes = {
    icon: PropTypes.node.isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
    onStart: PropTypes.func.isRequired,
};
