import React from 'react'
import PropTypes from 'prop-types'
import '../../PageComponents/CSS/SatQuestion.css'
import { InlineMath } from 'react-katex';

export default function SurvivalQuestion({ 
    question, 
    index, 
    selectedAnswer, 
    handleAnswerSelect,
    showFeedback = false,  // New prop to control when to show colors
    correctAnswer = null   // New prop for the correct answer
}) {

    const onChoiceClick = (answer) => {
        // Don't allow clicking after feedback is shown
        if (showFeedback) return;
        
        console.log("Selected answer: " + answer)
        handleAnswerSelect(question.id, answer)
    }

    const getChoiceClassName = (key) => {
        let className = 'choice-item';
        
        // If answer hasn't been selected yet
        if (!showFeedback) {
            if (selectedAnswer === key) {
                className += ' selected';
            }
        } 
        // If showing feedback
        else {
            if (key === correctAnswer) {
                className += ' correct';  // Green for correct answer
            } else if (selectedAnswer === key && key !== correctAnswer) {
                className += ' incorrect';  // Red for wrong answer
            }
        }
        
        return className;
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
                        className={getChoiceClassName(key)}
                        onClick={() => onChoiceClick(key)}
                        style={{ cursor: showFeedback ? 'not-allowed' : 'pointer' }}
                    >
                        <span className="choice-text">{parseText(value)}</span>
                    </div>
                ))}
            </div>
        </div>
    )
}

SurvivalQuestion.propTypes = {
    question: PropTypes.object.isRequired,
    index: PropTypes.number.isRequired,
    selectedAnswer: PropTypes.string,
    handleAnswerSelect: PropTypes.func.isRequired,
    showFeedback: PropTypes.bool,
    correctAnswer: PropTypes.string,
}
