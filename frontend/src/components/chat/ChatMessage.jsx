import React from 'react';
import ReactMarkdown from 'react-markdown';

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-in fade-in slide-in-from-bottom-2 duration-300`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-primary text-white rounded-tr-sm'
            : 'bg-gray-100 text-gray-900 rounded-tl-sm'
        } ${message.isError ? 'border border-red-200 bg-red-50 text-red-800' : ''}`}
      >
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="chat-markdown text-sm leading-relaxed">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
        {message.attachments && message.attachments.length > 0 && (
          <div className="mt-2 pt-2 border-t border-white/20">
            {message.attachments.map((file, i) => (
              <div key={i} className="flex items-center gap-1.5 text-xs opacity-80">
                <span>📎</span>
                <span>{file.name}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
