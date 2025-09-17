import useTypewriter from './typewriter.jsx';
import ReactMarkdown from 'react-markdown';
import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

export default function StreamingMessage({ response, onComplete }) {
    const { displayText, isTyping } = useTypewriter(response, 5);
    const messageEndRef = useRef(null);
    
    // Scroll every time new text appears
    useEffect(() => {
        if (messageEndRef.current) {
            messageEndRef.current.scrollIntoView({ 
                behavior: 'smooth',
                block: 'nearest'
            });
        }
    }, [displayText]);
    
    // When typing is complete, call onComplete to update status
    useEffect(() => {
        if (!isTyping && response && displayText === response) {
            onComplete();
        }
    }, [isTyping, response, displayText, onComplete]);

    return (
        <div>
            <ReactMarkdown>{displayText}</ReactMarkdown>
            {isTyping && <span className="cursor">|</span>}
            <div ref={messageEndRef} />
        </div>
    );
}

StreamingMessage.propTypes = {
    response: PropTypes.string.isRequired,
    onComplete: PropTypes.func.isRequired
};
