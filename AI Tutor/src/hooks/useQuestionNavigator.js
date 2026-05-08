import { useState } from 'react';

export function useQuestionNavigator() {
    const [currentIndex, setCurrentIndex] = useState(0);

    const resetQuestionIndex = () => {
        setCurrentIndex(0);
    };

    const selectNextQuestion = (questionCount) => {
        setCurrentIndex((index) => {
            if (index >= questionCount - 1) {
                return index;
            }

            return index + 1;
        });
    };

    const selectPreviousQuestion = () => {
        setCurrentIndex((index) => {
            if (index <= 0) {
                return index;
            }

            return index - 1;
        });
    };

    return {
        currentIndex,
        resetQuestionIndex,
        selectNextQuestion,
        selectPreviousQuestion,
    };
}
