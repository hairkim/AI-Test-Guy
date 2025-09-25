//this is the component for each sat question that will be shown
//it will have the question text, answer choices and will track score based on right answer in the dataset
//thought process: have a prop that represents the sat question object for this component
//how to track score? have a state variable that is updated when the user answers the question

import React from 'react'
import PropTypes from 'prop-types'
import '../CSS/SatQuestion.css'
import { InlineMath } from 'react-katex';

export default function SatQuestion({ question, index, selectedAnswer, handleAnswerSelect }) {

    const onChoiceClick = (answer) => {
        console.log("Selected answer: " + answer)
        handleAnswerSelect(question.id, answer)
    }


    const parseText = (text) => {
        return text.split(/(\$[^$]*\$)/g).map((part, i) =>
            part.startsWith('$') && part.endsWith('$') ? (
            <InlineMath key={i} math={part.slice(1, -1)} />
            ) : (
            <span key={i}>{part}</span>
            )
        )
    }

    return (
        <div className="sat-question">
            <div className="question-number">{index}.</div>
            {question.paragraph && <p className="paragraph">{question.paragraph}</p>}
            <p className="question-text">{parseText(question.question_text)}</p>
            
            <div className="choices-container">
                {Object.entries(question.choices).map(([key, value]) => (
                    <div 
                        key={key}
                        className={`choice-item ${selectedAnswer === key ? 'selected' : ''}`}
                        onClick={() => onChoiceClick(key)}
                    >
                        <div className="bubble">
                            <div className="bubble-inner">
                                {selectedAnswer === key && <div className="bubble-fill" />}
                            </div>
                            <span className="choice-letter">{key}</span>
                        </div>
                        <span className="choice-text">{parseText(value)}</span>
                    </div>
                ))}
            </div>
            {question.correct_answer && <p className="correct-answer">Correct Answer: {question.correct_answer}</p>}
            {/* {selectedAnswer && (
                <p className="selected-answer">Selected Answer: {selectedAnswer}</p>
            )} */}
        </div>
    )
}

SatQuestion.propTypes = {
    question: PropTypes.object.isRequired,
    index: PropTypes.number.isRequired,
    selectedAnswer: PropTypes.string,
    handleAnswerSelect: PropTypes.func.isRequired,
}