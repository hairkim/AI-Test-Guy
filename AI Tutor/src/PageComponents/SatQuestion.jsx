//this is the component for each sat question that will be shown
//it will have the question text, answer choices and will track score based on right answer in the dataset
//thought process: have a prop that represents the sat question object for this component
//how to track score? have a state variable that is updated when the user answers the question

import React, { useState } from 'react'
import PropTypes from 'prop-types'
import './SatQuestion.css'

export default function SatQuestion({ question, index }) {
    const [selectedAnswer, setSelectedAnswer] = useState(null)

    const handleAnswerSelect = (answer) => {
        setSelectedAnswer(answer)
    }

    return (
        <div className="sat-question">
            <div className="question-number">{index}.</div>
            {question.paragraph && <p className="paragraph">{question.paragraph}</p>}
            <p className="question-text">{question.question_text}</p>
            
            <div className="choices-container">
                {Object.entries(question.choices).map(([key, value]) => (
                    <div 
                        key={key}
                        className={`choice-item ${selectedAnswer === key ? 'selected' : ''}`}
                        onClick={() => handleAnswerSelect(key)}
                    >
                        <div className="bubble">
                            <div className="bubble-inner">
                                {selectedAnswer === key && <div className="bubble-fill" />}
                            </div>
                            <span className="choice-letter">{key}</span>
                        </div>
                        <span className="choice-text">{value}</span>
                    </div>
                ))}
            </div>
            
            {selectedAnswer && (
                <p className="selected-answer">Selected Answer: {selectedAnswer}</p>
            )}
        </div>
    )
}

SatQuestion.propTypes = {
    question: PropTypes.object.isRequired,
}