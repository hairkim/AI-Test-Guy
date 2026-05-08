import { useState } from 'react';

export function useTimerWarning() {
    const [timerWarning, setTimerWarning] = useState('');

    const showTimerWarning = (message) => {
        setTimerWarning(message);
        setTimeout(() => setTimerWarning(''), 5000);
    };

    return {
        timerWarning,
        showTimerWarning,
    };
}
