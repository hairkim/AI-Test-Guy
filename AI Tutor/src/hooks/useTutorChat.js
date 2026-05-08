import { useEffect, useRef, useState } from 'react';

export function useTutorChat({
    buildUserMessage,
    emptyPromptError,
    submitRequest,
    validatePrompt,
}) {
    const [prompt, setPrompt] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [chatHistory, setChatHistory] = useState([]);
    const [userHasScrolled, setUserHasScrolled] = useState(false);
    const chatContainerRef = useRef(null);
    const lastScrollTop = useRef(0);

    useEffect(() => {
        const container = chatContainerRef.current;
        if (!container) return;

        const handleScroll = () => {
            const currentScrollTop = container.scrollTop;

            if (currentScrollTop < lastScrollTop.current) {
                setUserHasScrolled(true);
            }

            const { scrollTop, scrollHeight, clientHeight } = container;
            if (scrollTop + clientHeight >= scrollHeight - 25) {
                setUserHasScrolled(false);
            }

            lastScrollTop.current = currentScrollTop;
        };

        container.addEventListener('scroll', handleScroll, { passive: true });
        return () => container.removeEventListener('scroll', handleScroll);
    }, []);

    useEffect(() => {
        if (!userHasScrolled && chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [chatHistory, userHasScrolled]);

    const submitPrompt = async (context = {}) => {
        if (!validatePrompt({ prompt, ...context })) {
            setError(emptyPromptError);
            return;
        }

        setUserHasScrolled(false);

        const pendingMessage = {
            ...buildUserMessage({ prompt, ...context }),
            response: null,
            timestamp: new Date().toISOString(),
            status: 'pending',
        };
        setChatHistory((prev) => [...prev, pendingMessage]);

        const currentPrompt = prompt;
        setPrompt('');
        setIsLoading(true);
        setError('');

        try {
            const data = await submitRequest({ prompt: currentPrompt, ...context });
            const response = data.solution || '';

            setChatHistory((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    response,
                    status: 'streaming',
                };
                return updated;
            });
        } catch (err) {
            setChatHistory((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    status: 'error',
                };
                return updated;
            });
            setError(`Server error: ${err.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleTypingComplete = (messageIndex) => {
        setChatHistory((prev) => {
            const updated = [...prev];
            updated[messageIndex].status = 'complete';
            return updated;
        });
    };

    const handleKeyDown = (event, context = {}) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            submitPrompt(context);
        }
    };

    return {
        chatContainerRef,
        chatHistory,
        error,
        handleKeyDown,
        handleTypingComplete,
        isLoading,
        prompt,
        setError,
        setPrompt,
        submitPrompt,
    };
}
