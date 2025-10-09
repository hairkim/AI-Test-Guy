import useTypewriter from './typewriter.jsx';
import ReactMarkdown from 'react-markdown';
import React, { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

export default function StreamingMessage({ response, onComplete }) {
    const { displayText, isTyping } = useTypewriter(response, 5);
    const messageEndRef = useRef(null);
    const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
    
    // Check if user is near bottom of scroll container
    const checkScrollPosition = () => {
        const chatContainer = document.querySelector('.english_qpage_messages_main_container');
        if (!chatContainer) return true;
        
        const { scrollTop, scrollHeight, clientHeight } = chatContainer;
        const threshold = 50; // pixels from bottom
        const isNearBottom = scrollTop + clientHeight >= scrollHeight - threshold;
        
        setShouldAutoScroll(isNearBottom);
    };
    
    // Add scroll listener to chat container when component mounts
    useEffect(() => {
        const chatContainer = document.querySelector('.english_qpage_messages_main_container');
        if (chatContainer) {
            chatContainer.addEventListener('scroll', checkScrollPosition);
            return () => chatContainer.removeEventListener('scroll', checkScrollPosition);
        }
    }, []);
    
    // Only auto-scroll if user is near bottom
    useEffect(() => {
        if (shouldAutoScroll && messageEndRef.current) {
            messageEndRef.current.scrollIntoView({ 
                behavior: 'smooth',
                block: 'nearest'
            });
        }
    }, [displayText, shouldAutoScroll]);
    
    // When typing is complete, call onComplete to update status
    useEffect(() => {
        if (!isTyping && response && displayText === response) {
            onComplete();
        }
    }, [isTyping, response, displayText, onComplete]);

    return (
        <div>
            <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>{displayText}</ReactMarkdown>
            {isTyping && <span className="cursor">|</span>}
            <div ref={messageEndRef} />
        </div>
    );
}

StreamingMessage.propTypes = {
    response: PropTypes.string.isRequired,
    onComplete: PropTypes.func.isRequired
};