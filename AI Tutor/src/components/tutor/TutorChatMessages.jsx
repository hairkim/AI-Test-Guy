import PropTypes from 'prop-types';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import StreamingMessage from './StreamingMessage.jsx';

export default function TutorChatMessages({
    chatHistory,
    emptyMessage,
    emptyStateClassName,
    messageContainerClassName,
    onTypingComplete,
}) {
    if (chatHistory.length === 0) {
        return (
            <div className={emptyStateClassName}>
                <div>{emptyMessage}</div>
            </div>
        );
    }

    return chatHistory.map((message, index) => (
        <div className={messageContainerClassName} key={`${message.timestamp}-${index}`}>
            <div className="message-wrapper user">
                <div className="chat_box_user_message">
                    {message.question}
                    {message.hasImage && (
                        <div className="image-indicator">📷 Image attached</div>
                    )}
                </div>
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
                            {message.response}
                        </ReactMarkdown>
                    )}
                </div>
            </div>
        </div>
    ));
}

TutorChatMessages.propTypes = {
    chatHistory: PropTypes.arrayOf(PropTypes.object).isRequired,
    emptyMessage: PropTypes.string.isRequired,
    emptyStateClassName: PropTypes.string.isRequired,
    messageContainerClassName: PropTypes.string.isRequired,
    onTypingComplete: PropTypes.func.isRequired,
};
