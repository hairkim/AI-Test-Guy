import PropTypes from 'prop-types';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import StreamingMessage from '../tutor/StreamingMessage.jsx';

export default function PracticeTutorChat({
    chatHistory,
    error,
    isLoading,
    onBackToPractice,
    onKeyDown,
    onSubmit,
    onTypingComplete,
    onUserQuestionChange,
    points,
    userQuestion,
}) {
    return (
        <div className="ai_container">
            <div className="ai_header">
                <h2>AI Tutor</h2>
                <p>{points}</p>
            </div>
            <div className="ai_messages_container">
                {chatHistory.length === 0 && (
                    <div className="welcome-message">
                        <p>👋 Hi! I&apos;m your SAT tutor. I can help you with this question by:</p>
                        <ul>
                            <li>Giving you hints to guide your thinking</li>
                            <li>Checking your reasoning</li>
                            <li>Explaining key concepts</li>
                            <li>Breaking down the problem step-by-step</li>
                        </ul>
                        <p>Just ask me anything or use the quick action buttons above!</p>
                    </div>
                )}

                {chatHistory.map((message, index) => (
                    <div className="qpage_messages_container" key={`${message.timestamp}-${index}`}>
                        <div className="message-wrapper user">
                            <div className="chat_box_user_message">{message.user}</div>
                        </div>

                        <div className="message-wrapper ai">
                            <div className="chat_box_ai_message">
                                {message.status === 'pending' ? (
                                    <div className="typing-indicator">Loading...</div>
                                ) : message.status === 'streaming' ? (
                                    <StreamingMessage
                                        response={message.response}
                                        onComplete={() => onTypingComplete(index)}
                                    />
                                ) : message.status === 'error' ? (
                                    <div>Sorry, I couldn&apos;t process that request.</div>
                                ) : (
                                    <ReactMarkdown
                                        remarkPlugins={[remarkMath]}
                                        rehypePlugins={[rehypeKatex]}
                                    >
                                        {message.tutor}
                                    </ReactMarkdown>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
            <div className="qpage_form">
                {error && (
                    <div className="error-message">
                        <p>{error}</p>
                        <button type="button" onClick={onBackToPractice}>
                            Back to Practice
                        </button>
                    </div>
                )}
                <div className="input-wrapper">
                    <textarea
                        className="prompt auto-resize"
                        value={userQuestion}
                        onChange={(event) => onUserQuestionChange(event.target.value)}
                        onKeyDown={onKeyDown}
                        placeholder="Ask me anything..."
                        disabled={isLoading}
                        rows={1}
                    />
                    <button
                        className="submit-button"
                        onClick={onSubmit}
                        disabled={isLoading || !userQuestion.trim()}
                    >
                        {isLoading ? '⏳' : '➤'}
                    </button>
                </div>
            </div>
        </div>
    );
}

PracticeTutorChat.propTypes = {
    chatHistory: PropTypes.arrayOf(PropTypes.object).isRequired,
    error: PropTypes.string.isRequired,
    isLoading: PropTypes.bool.isRequired,
    onBackToPractice: PropTypes.func.isRequired,
    onKeyDown: PropTypes.func.isRequired,
    onSubmit: PropTypes.func.isRequired,
    onTypingComplete: PropTypes.func.isRequired,
    onUserQuestionChange: PropTypes.func.isRequired,
    points: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
    userQuestion: PropTypes.string.isRequired,
};
