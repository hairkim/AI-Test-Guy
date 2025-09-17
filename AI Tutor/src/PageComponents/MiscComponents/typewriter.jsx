import React, { useState, useEffect } from 'react';

const useTypewriter = (text, speed = 50) => {
    const [displayText, setDisplayText] = useState('');
    const [isTyping, setIsTyping] = useState(false);

    useEffect(() => {
        if (!text) return;
        
        setIsTyping(true);
        setDisplayText('');
        let index = 0;

        const timer = setInterval(() => {
            if (index < text.length) {
                setDisplayText(text.slice(0, index + 1));
                index++;
            } else {
                setIsTyping(false);
                clearInterval(timer);
            }
        }, speed);

        return () => clearInterval(timer);
    }, [text, speed]);

    return { displayText, isTyping };
};

export default useTypewriter;